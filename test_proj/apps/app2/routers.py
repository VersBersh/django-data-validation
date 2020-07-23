
class App2Router:
    """ routes app2 to the postgres2 database """

    app_label = "app2"
    db = "postgres2"

    def db_for_read(self, model, **hints):
        if model._meta.app_label == self.app_label:
            return self.db
        return None

    def db_for_write(self, model, **hints):
        if model._meta.app_label == self.app_label:
            return self.db
        return None

    @staticmethod
    def allow_relation(obj1, obj2, **hints):
        return True

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """Make sure SecondDatabase only appears on the db"""
        if db == self.db:
            return app_label == self.app_label
        elif app_label == self.app_label:
            return False
        return None
