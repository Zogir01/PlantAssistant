from .singleton import singleton
import ujson
import time
import os

CONFIG_PATH = "config"

class ConfigFile:
    def __init__(self, filepath):
        """ Loads or creates .json file with specified name under directory 
        defined in `CONFIG_PATH` module constant.

        Filepath is determined as `{CONFIG_PATH}/{name}.json`. 
        If directory with `CONFIG_PATH` doesn't exist, it will be created.
        """
        self._filepath = filepath
        self._buffer = {}
        self._need_save = False

        try:
            with open(self._filepath, "r") as f:
                self._buffer = ujson.load(f)
        except:
            try:
                with open(self._filepath, "w") as f:
                    ujson.dump(self._buffer, f)
            except:
                pass

    @property
    def need_save(self):
        """ Returns an flag which signals that there is unsaved data in the buffer. """
        return self._need_save

    # https://stackoverflow.com/questions/13687924/setting-a-value-in-a-nested-python-dictionary-given-a-list-of-indices-and-value
    def get(self, *keys, default=None, required=False):
        """Access nested config value. Raises KeyError if `required=True` and key not found."""
        if not keys:
            return self._buffer
        
        cp = self._buffer
        for key in keys[:-1]:
            if key not in cp:
                if required:
                    raise KeyError(f"Intermediate key '{key}' not found (keys={keys})")
                return default
            cp = cp[key]

        last_key = keys[-1]
        if required and last_key not in cp:
            raise KeyError(f"Item not found (keys={keys})")
        
        return cp.get(last_key, default)
    
    def set(self, *keys, value):
        """ Pass nested keys of an element to set the value given in keyword param `value`. 

        Ensure that passed value is correct to be serialized into JSON.
        For example: python allows keys to be integer, but in JSON format keys must be string type.
        """
        cp = self._buffer
        for key in keys[:-1]:
            cp = cp.setdefault(key, {})
        cp[keys[-1]] = value
        self._need_save = True
        
    def save(self):
        """
        """
        try:
            with open(self._filepath, "w") as f:
                ujson.dump(self._buffer, f)
            self._need_save = False
        except: pass

    def __str__(self):
        return f"buffer: {self._buffer}, saved: {not self.need_save}"

@singleton
class ConfigManager:
    def __init__(self):
        """ Initializing dictionary of `ConfigFile` objects from filepaths determined from real 
        files located in config directory path defined in `CONFIG_PATH` module constant.

        Filepath is determined as `{CONFIG_PATH}/{name}.json` where `name` is the key in this dictionary
        and `ConfigFile` is the value.
        
        If directory with `CONFIG_PATH` doesn't exist, it will be created.
        """
        self._configs = {}

        try:
            os.mkdir(CONFIG_PATH) # uPython specific
        except: 
            pass # directory exists

        for filename in os.listdir(CONFIG_PATH):
            name = filename.split('.')[0]
            self.register_config(name)

    def register_config(self, name) -> ConfigFile:
        """ Creates and returns new `ConfigFile` object. 
        Returns none if ConfigFile with provided name is already in dictionary.

        New item will be added to internal dictionary for easy access to this
        object from ConfigManager singleton.
        """
        if self._configs.get(name) is None:
            self._configs[name] = ConfigFile(f"{CONFIG_PATH}/{name}.json")
            return self._configs[name]
        else: 
            return None
    
    def get_config(self, name) -> ConfigFile:
        """ Returns `ConfigFile` object by its `name` or `None` if not found. """
        return self._configs.get(name)
    
    def save(self):
        """ Call the `save` methods for all stored ConfigFile objects. """
        for c in self._configs.values():
            c.save()

# Example code
if __name__ == '__main__':
    # TO-DO
    pass




