-- Designed by Dmytro Fedorov, 2025
-- Recognized for asterisk,mysql data base;
-- The trigger is designed to filter, group, and record “missed call” events in a readable 
-- format in the <tg_notification_mc_queue> table for further integration with a script for 
-- sending notifications to a telegram group. 

DELIMITER $$

CREATE TRIGGER trg_after_insert_queue_log
AFTER INSERT ON queue_log
FOR EACH ROW
BEGIN
    -- declare variables
    DECLARE v_date DATETIME;
    DECLARE v_number VARCHAR(12);
    DECLARE v_client_description VARCHAR(255) DEFAULT 'Client is undefined';

    -- check whether the event is EXITWITHTIMEOUT or ABANDON
    IF NEW.event IN ('EXITWITHTIMEOUT', 'ABANDON') THEN
        -- Get date
        SET v_date = NOW();

        -- Get phone-number, using callid and event = 'ENTERQUEUE'
        BEGIN
            DECLARE CONTINUE HANDLER FOR NOT FOUND SET v_number = NULL;
            SELECT data2
            INTO v_number
            FROM queue_log
            WHERE callid = NEW.callid AND event = 'ENTERQUEUE'
            ORDER BY time DESC
            LIMIT 1;
        END;

        -- Serch client in table customers
        IF v_number IS NOT NULL THEN
            BEGIN
                DECLARE CONTINUE HANDLER FOR NOT FOUND SET v_client_description = 'Client is undefined';
                SELECT description
                INTO v_client_description
                FROM customers
                WHERE phone = v_number COLLATE utf8_unicode_ci
                LIMIT 1;
            END;

            -- Add record in table tg_notification_mc_queue
            INSERT INTO tg_notification_mc_queue (date, number, client_description)
            VALUES (v_date, v_number, v_client_description);
        END IF;
    END IF;
END$$

DELIMITER ;
