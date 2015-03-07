ALTER TABLE ekatte
ADD FOREIGN KEY (oblast)
REFERENCES oblast(oblast);

ALTER TABLE ekatte 
ADD FOREIGN KEY (obshtina)
REFERENCES obshtina(obshtina);

ALTER TABLE ekatte
ADD FOREIGN KEY (kmetstvo)
REFERENCES kmetstvo(kmetstvo);

ALTER TABLE oblast
ADD FOREIGN KEY (region)
REFERENCES region(region);