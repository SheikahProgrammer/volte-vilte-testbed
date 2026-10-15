-- ==============================================================================
-- PyHSS MySQL Database Initialization for VoLTE/ViLTE COTS UE Provisioning
-- Matches sample_subscribers.json with test PLMN 001-01 and sanitized test keys
-- Reference: Section III-B (Dual-Database Provisioning)
-- ==============================================================================

USE `ims_hss_db`;

--
-- Clean existing sample data
--
DELETE FROM `ims_subscriber` WHERE `msisdn` IN ('1001', '1002');
DELETE FROM `subscriber` WHERE `imsi` IN ('001010000000001', '001010000000002');
DELETE FROM `auc` WHERE `imsi` IN ('001010000000001', '001010000000002');

--
-- Table structure: auc (Authentication Center credentials)
--
INSERT INTO `auc` (`auc_id`, `ki`, `opc`, `amf`, `sqn`, `imsi`) VALUES
(1, '00112233445566778899aabbccddeeff', '000102030405060708090a0b0c0d0e0f', '8000', 1000, '001010000000001'),
(2, '00112233445566778899aabbccddeeff', '000102030405060708090a0b0c0d0e0f', '8000', 1000, '001010000000002')
ON DUPLICATE KEY UPDATE `ki`=VALUES(`ki`), `opc`=VALUES(`opc`);

--
-- Table structure: subscriber (Core Network & IMS subscriber profile)
--
INSERT INTO `subscriber` (`subscriber_id`, `imsi`, `enabled`, `auc_id`, `default_apn`, `apn_list`, `msisdn`, `ue_ambr_dl`, `ue_ambr_ul`, `subscribed_rau_tau_timer`) VALUES
(1, '001010000000001', 1, 1, 1, '1,2', '1001', 100000000, 50000000, 300),
(2, '001010000000002', 1, 2, 1, '1,2', '1002', 100000000, 50000000, 300)
ON DUPLICATE KEY UPDATE `enabled`=VALUES(`enabled`), `msisdn`=VALUES(`msisdn`);

--
-- Table structure: ims_subscriber (IMPI, IMPU, and Initial Filter Criteria bindings)
--
INSERT INTO `ims_subscriber` (`ims_subscriber_id`, `msisdn`, `msisdn_list`, `impu`, `impi`, `scscf_peer`, `pcscf_peer`) VALUES
(1, '1001', '1001', 'sip:1001@ims.mnc001.mcc001.3gppnetwork.org', '001010000000001@ims.mnc001.mcc001.3gppnetwork.org', 'scscf.ims.mnc001.mcc001.3gppnetwork.org', 'pcscf.ims.mnc001.mcc001.3gppnetwork.org'),
(2, '1002', '1002', 'sip:1002@ims.mnc001.mcc001.3gppnetwork.org', '001010000000002@ims.mnc001.mcc001.3gppnetwork.org', 'scscf.ims.mnc001.mcc001.3gppnetwork.org', 'pcscf.ims.mnc001.mcc001.3gppnetwork.org')
ON DUPLICATE KEY UPDATE `impu`=VALUES(`impu`), `impi`=VALUES(`impi`);
