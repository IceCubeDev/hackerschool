__author__ = 'Ivan Dortulov'

from PydbSimple import PydbSimple


def main():
    db = PydbSimple()

    db.create_table("test_table", [{"column_name": "int1",
                                    "column_type": PydbSimple.INTEGER},
                                   {"column_name": "int2",
                                    "column_type": PydbSimple.INTEGER},
                                   {"column_name": "int3",
                                    "column_type": PydbSimple.INTEGER},
                                   {"column_name": "int4",
                                    "column_type": PydbSimple.INTEGER},
                                   {"column_name": "int5",
                                    "column_type": PydbSimple.INTEGER},
                                   {"column_name": "str1k",
                                    "column_type": PydbSimple.STRING},
                                   {"column_name": "str10k",
                                    "column_type": PydbSimple.STRING},
                                   {"column_name": "str100k",
                                    "column_type": PydbSimple.STRING}])

if __name__ == "__main__":
    main()