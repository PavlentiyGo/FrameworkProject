-- name: rooms
-- 1. Список помещений. LEFT JOIN сохраняет помещения без устройств.
SELECT r.id, r.name, COUNT(d.id) AS device_count
FROM rooms AS r
LEFT JOIN devices AS d ON d.room_id = r.id
GROUP BY r.id, r.name
ORDER BY r.name, r.id;

-- name: devices
-- 2. Список техники с названиями помещения и состояния (два JOIN).
SELECT d.*, r.name AS room_name, c.name AS condition
FROM devices AS d
JOIN rooms AS r ON r.id = d.room_id
JOIN conditions AS c ON c.id = d.condition_id
ORDER BY d.name, d.id;

-- name: room
-- 3. Помещение по идентификатору. Параметр: room_id.
SELECT id, name FROM rooms WHERE id = ?;

-- name: device
-- 4. Подробная информация об устройстве. Параметр: device_id.
SELECT d.*, r.name AS room_name, c.name AS condition
FROM devices AS d
JOIN rooms AS r ON r.id = d.room_id
JOIN conditions AS c ON c.id = d.condition_id
WHERE d.id = ?;

-- name: room_devices
-- 5. Техника выбранного помещения. Параметр: room_id.
SELECT d.*, r.name AS room_name, c.name AS condition
FROM devices AS d
JOIN rooms AS r ON r.id = d.room_id
JOIN conditions AS c ON c.id = d.condition_id
WHERE d.room_id = ?
ORDER BY d.name, d.id;

-- name: conditions
-- 6. Справочник состояний для формы поиска.
SELECT id, name FROM conditions ORDER BY id;

-- name: search_devices
-- 7. Поиск по нескольким полям и фильтры. Значения передаются через ?.
-- Параметры: шаблон q (трижды), room_id (дважды), condition (дважды),
-- max_price (дважды). NULL означает отсутствие соответствующего фильтра.
SELECT d.*, r.name AS room_name, c.name AS condition
FROM devices AS d
JOIN rooms AS r ON r.id = d.room_id
JOIN conditions AS c ON c.id = d.condition_id
WHERE (d.name LIKE ? ESCAPE '\' OR d.device_type LIKE ? ESCAPE '\'
       OR d.manufacturer LIKE ? ESCAPE '\')
  AND (? IS NULL OR d.room_id = ?)
  AND (? IS NULL OR c.name = ?)
  AND (? IS NULL OR d.price <= ?)
ORDER BY d.name, d.id;

-- name: device_totals
-- 8. Сводная статистика. Списанная техника не включается в стоимость.
SELECT COUNT(*) AS total_devices,
       COALESCE(SUM(CASE WHEN c.name != 'списано' THEN d.price END), 0)
           AS total_price,
       COALESCE(AVG(CASE WHEN c.name != 'списано' THEN d.price END), 0)
           AS average_price,
       MIN(d.purchase_year) AS oldest_year,
       MAX(d.purchase_year) AS newest_year,
       COALESCE(SUM(c.name = 'исправно'), 0) AS available_count
FROM devices AS d
JOIN conditions AS c ON c.id = d.condition_id;

-- name: room_statistics
-- 9. Группировка по помещениям и HAVING. Параметр: минимум устройств.
-- COUNT(d.id), а не COUNT(*), даёт ноль для пустого помещения.
SELECT r.id, r.name, COUNT(d.id) AS device_count,
       COALESCE(SUM(CASE WHEN c.name != 'списано' THEN d.price END), 0)
           AS total_price
FROM rooms AS r
LEFT JOIN devices AS d ON d.room_id = r.id
LEFT JOIN conditions AS c ON c.id = d.condition_id
GROUP BY r.id, r.name
HAVING COUNT(d.id) >= ?
ORDER BY device_count DESC, r.name;

-- name: condition_statistics
-- 10. Группировка по состояниям, включая состояния без устройств.
SELECT c.id, c.name, COUNT(d.id) AS device_count,
       COALESCE(SUM(d.price), 0) AS total_price
FROM conditions AS c
LEFT JOIN devices AS d ON d.condition_id = c.id
GROUP BY c.id, c.name
ORDER BY c.id;

-- name: service_due
-- 11. Техника, требующая обслуживания. Параметр: текущий год.
-- Списанное и уже ремонтируемое оборудование в этот список не попадает.
SELECT d.id, d.name, r.name AS room_name, c.name AS condition
FROM devices AS d
JOIN rooms AS r ON r.id = d.room_id
JOIN conditions AS c ON c.id = d.condition_id
WHERE c.name NOT IN ('списано', 'в ремонте')
  AND (c.name = 'требует обслуживания'
       OR ? - d.purchase_year >= d.service_interval)
ORDER BY d.purchase_year, d.name;

-- name: empty_rooms
-- 12. Помещения без действующей техники: аналог поиска свободных мест.
-- Списанное устройство не делает помещение занятым.
SELECT r.id, r.name FROM rooms AS r
WHERE NOT EXISTS (
    SELECT 1 FROM devices AS d
    JOIN conditions AS c ON c.id = d.condition_id
    WHERE d.room_id = r.id AND c.name != 'списано'
)
ORDER BY r.name, r.id;
