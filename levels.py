

class Levels:
    def __init__(self):
        self.classes = {}

    def get_level(self, class_name: str):
        if class_name in self.classes:
            return self.classes[class_name]
        return 0

    def get_common_level(self):
        return sum(self.classes.values())