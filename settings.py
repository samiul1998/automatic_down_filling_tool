from PyQt6.QtCore import QSettings

def save_factory_info(name, location):
    settings = QSettings("DownAllocation", "FactoryInfo")
    settings.setValue("factory_name", name)
    settings.setValue("factory_location", location)

def load_factory_info():
    settings = QSettings("DownAllocation", "FactoryInfo")
    return (
        settings.value("factory_name", ""),
        settings.value("factory_location", "")
    )