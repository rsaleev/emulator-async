from tortoise import Tortoise

class DBConnector:

    def __init__(self):
        self.db = None
        
    async def connect(self):
        """connect [summary]

        [extended_summary]

        Returns:
            [type]: [description]
        """
        # Here we connect to a SQLite DB file.
        # also specify the app name of "models"
        # which contain models from "app.models"
        await Tortoise.init(
            db_url='sqlite://db.sqlite3',
            modules={'models': ['src.db.models.token', 'src.db.models.shift' ,'src.db.models.receipt', 'src.db.models.state']}
        )
        # Generate the schema
        await Tortoise.generate_schemas()
        self.db = Tortoise._connections
        return self