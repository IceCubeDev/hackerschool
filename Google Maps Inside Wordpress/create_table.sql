CREATE TABLE IF NOT EXISTS `markers` (
  `id` int(11) NOT NULL,
  `name` varchar(128) NOT NULL,
  `address` text NOT NULL,
  `lat` double NOT NULL,
  `lng` double NOT NULL,
  `description` text NOT NULL,
  `type` varchar(32) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8  DEFAULT COLLATE utf8_general_ci;
