import os


class ReadConfig:
    def __init__(self, conf_file):
        self.dev = "Absent"
        self.port = ''
        self.def_cat = ''
        self.port = ''
        self.impulses = 1

        self.conf_file = conf_file

        # headers for every sequence
        self.def_sample_headers = [
            "Key",
            "DateBegin",
            "DateEnd",
            "Length",
            "SapWood",
            "Bark",
            "Refs",
            "LabNotes",
        ]

        self.headers = [
            "KeyCode",
            "Species",
            # "DateBegin",
            # "DateEnd",
        ]
        self.lenOrgHeaders = len(self.headers)

        if not os.path.isfile(conf_file):
            return

        for raw in open(conf_file, 'r'):
            line = raw.rstrip('\r\n')
            tt = line.split('|')
            if tt[0] == "S":
                self.def_cat = tt[1]
            if tt[0] == "ST":
                self.impulses = int(tt[1])  # imp/mm
            if tt[0] == "E":  # headers order in tablewidget
                self.headers += [x for x in tt[1].split(',')
                                 if x not in self.headers]
            if tt[0] == "PORT":  # com or interface
                self.port = tt[1]
            if tt[0] == "LICZ":
                # counter type
                # "wo"- WOBIT counter
                # "pi" - AGH counter
                self.dev = tt[1]

    def write_config(self):
        '''Saves stored config to file in main catalog'''
        out = '\n'.join([
            'LICZ|'+self.dev,
            'PORT|'+self.port,
            'ST|'+str(self.impulses),
            'E|'+','.join(self.headers),
            'S|'+self.def_cat,
        ])

        cat = os.path.join(os.path.dirname(__file__),
                           self.conf_file)
        fl = open(cat, 'w')
        fl.write(out)
        fl.close()
