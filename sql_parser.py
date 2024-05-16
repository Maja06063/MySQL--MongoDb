class SqlParser():

    # Inicjalizacja słownika na strukturę i listy na zawartość tabel
    tables_structure = {} # słownik
    tables_content = [] # lista

    def get_tables_structure(self) -> dict:
        return self.tables_structure

    def get_tables_content(self) -> list:
        return self.tables_content

    # Funkcja tekst między przecinkami i zwraca słownik z nazwą i typem zmiennej oraz jej dodatkowymi parametrami
    def __parse_attribute(self, attribute_string):
        attribute = {}
        attribute["name"] = attribute_string.split(" ")[0]
        attribute["type"] = attribute_string.split(" ")[1]
        attribute["info"] = " ".join(attribute_string.split(" ")[2:])

        return attribute

    # Funkcja do parsowania definicji tabeli
    def parse_create_table(self, query):

        # Wyszukiwanie nazwy tabeli za pomocą metody split
        table_name = query.split("(")[0].strip().split(" ")[-1]
        if table_name:
            # Parsowanie atrybutów tabeli również za pomocą wyrażenia regularnego
            attributes = []
            attributes_begin_index = query.find("(") # szuka numeru na którym stoi ( w liście query (bo string to lista znakow)
            attributes_string_list = query[attributes_begin_index+1:-2].split(",") # bierze tylko elementy w nawiasie (+1 i -1 by nie brac nawiasow) i dzieli je po ,
            for i in range (len(attributes_string_list)-1):
                if "(" in attributes_string_list[i] and ")" not in attributes_string_list[i]:
                    for j in range(i+1, len(attributes_string_list)):
                        attributes_string_list[i]+="," + attributes_string_list[j]
                        attributes_string_list[j]=""
                        if ")" in attributes_string_list[i+1]:
                            break
            attributes_string_list = [i for i in attributes_string_list if i] # usuwanie pustych stringów z listy


            for attribute_string in attributes_string_list:

                attribute_string = attribute_string.strip()
                if attribute_string.startswith("PRIMARY KEY") or attribute_string.startswith("FOREIGN KEY"):
                    continue

                attributes.append(self.__parse_attribute(attribute_string))

            # Zwracamy nazwę tabeli i listę atrybutów
            return table_name, attributes
        # Jeśli nie udało się znaleźć nazwy tabeli, zwracamy None
        return None, None

    def __parse_text_after_values_keyword(self, text_after_values) -> list:

        all_records_list = []
        while True:

            begin = text_after_values.find('(')
            end = text_after_values.find(')')

            if begin == -1 or end == -1:
                break

            record_string = text_after_values[begin + 1:end]
            record_list = record_string.split(',')

            #usuwanie bialych niepotrzebnych znakow w nazwach kolumn
            for i in range(len(record_list)):
                record_list[i]=record_list[i].strip()
                if record_list[i][0]=="'" and record_list[i][-1]== "'":
                    record_list[i]=record_list[i][1:-1]
            all_records_list.append(record_list)

            text_after_values = text_after_values[end+1:]

        return all_records_list

    # Funkcja do parsowania instrukcji INSERT INTO zwraca liste
    def parse_insert_into(self, query) -> list:

        word_list = query.split()

        #SZUKANIE NAZWY TABELI - Jezeli 1 wyraz to insert, 2 into, to 3 to jest nazwa tabeli
        table_name = ""
        for i in range(len(word_list)-2):
            if word_list[i].upper()== 'INSERT' and word_list[i+1].upper() == 'INTO':
                table_name = word_list[i+2]

        # podzielenie zapytania na 2 czesci (przed VALUES i po)
        text_before_values = query.split('VALUES')[0]
        attibutes_list = text_before_values[text_before_values.find('(')+1:text_before_values.find(')')].split(',')
        #usuwanie bialych niepotrzebnych znakow w nazwach kolumn
        for i in range(len(attibutes_list)):
            attibutes_list[i]=attibutes_list[i].strip()

        # podzielenie zapytania na 2 czesci (przed VALUES i po)
        text_after_values = query.split('VALUES')[1]
        all_records_list = self.__parse_text_after_values_keyword(text_after_values)

        final_list = []
        for record_list in all_records_list:

            record = {
                "table_name": table_name,
                "attributes": {}
            }
            for i in range(len(attibutes_list)):
                record["attributes"][attibutes_list[i]]=record_list[i]

            final_list.append(record)

        return final_list

    def parse(self, sql_script: str):

        # Podział skryptu na instrukcje
        sql_instructions = sql_script.split(';')

        # Parsowanie i budowanie słowników
        for instruction in sql_instructions:
            # Usunięcie białych znaków z początku i końca instrukcji
            instruction = instruction.strip()

            # Usuwanie komentarzy: (kończą się znakiem końca linii)
            lines = instruction.split("\n")
            instruction = ""
            for line in lines:
                if not line.startswith("--"):
                    instruction += line + "\n"

            if instruction.startswith('CREATE TABLE'):
                # Jeśli instrukcja rozpoczyna się od "CREATE TABLE", parsujemy definicję tabeli
                table_name, attributes = self.parse_create_table(instruction)
                if table_name and attributes:
                    # Dodajemy informacje o strukturze tabeli do słownika tables_structure
                    self.tables_structure[table_name] = attributes
            elif instruction.startswith('INSERT INTO'):
                # Jeśli instrukcja rozpoczyna się od "INSERT INTO", parsujemy instrukcję wstawiania
                records = self.parse_insert_into(instruction)
                if records:
                    self.tables_content.extend(records)