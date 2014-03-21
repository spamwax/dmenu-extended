# -*- coding: utf8 -*-
import commands
import sys
import os
import subprocess
import signal
import json
import urllib2
import signal
import time

path_base = os.path.expanduser('~') + '/.config/dmenu-extended'

filename_preferences = "user_preferences.conf"
filename_configuration = "configuration.conf"

default_config = {
    "dmenu_args": [
        "-b",
        "-i",
        "-nf",
        "#888888",
        "-nb",
        "#1D1F21",
        "-sf",
        "#ffffff",
        "-sb",
        "#1D1F21",
        "-fn",
        "Terminus:12",
        "-l",
        "30"
    ],
    "fileopener": "xdg-open",
    "filebrowser": "xdg-open",
    "webbrowser": "xdg-open",
    "terminal": "xterm",
    "submenu_indicator": "* ",
}

default_prefs = {
    "valid_extensions": [
        "py",
        "svg",
        "pdf",
        "txt",
        "png",
        "jpg",
        "gif",
        "php",
        "tex",
        "odf",
        "ods",
        "avi",
        "mpg",
        "mp3",
        "lyx",
        "bib",
        "iso",
        "ps",
        "zip",
        "xcf"
    ],

    "watch_folders": ["~/"],

    "exclude_folders": [],

    "include_items": [],

    "filter_binaries": True,

    "follow_simlinks": True
}

def setup_user_files(path):

    print('Setting up dmenu-extended configuration files...')
    try:
        os.makedirs(path + '/plugins')
    except OSError:
        print('Target directory already exists - overwriting contents')
    print('Plugins folder created at: ' + path + '/plugins')

    # Change to nicer defaults
    if os.path.exists('/usr/bin/gnome-open'):
        default_config['fileopener'] = 'gnome-open'
        default_config['webbrowser'] = 'gnome-open'
        default_config['filebrowser'] = 'gnome-open'
    if os.path.exists('/usr/bin/urxvt'):
        default_config['terminal'] = 'urxvt'

    if os.path.exists(path + '/' + filename_configuration) == False:
        with open(path + '/' + filename_configuration,'w') as f:
            json.dump(default_config, f, sort_keys=True, indent=4)
        print('Configuration file created at: ' + path + '/' + filename_configuration)
    else:
        print('Existing configuration file found, will not overwrite.')

    if os.path.exists(path + '/' + filename_preferences) == False:
        with open(path + '/' + filename_preferences,'w') as f:
            json.dump(default_prefs, f, sort_keys=True, indent=4)
        print('user_preferences file created at: ' + path + '/' + filename_preferences)
    else:
        print('Existing user preferences file found, will not overwrite')

    # Create package __init__
    with open(path + '/plugins/__init__.py','w') as f:
        f.write('import os\n')
        f.write('import glob\n')
        f.write('__all__ = [ os.path.basename(f)[:-3] for f in glob.glob(os.path.dirname(__file__)+"/*.py")]')


if (os.path.exists(path_base + '/plugins') and
    os.path.exists(path_base + '/' + filename_configuration) and
    os.path.exists(path_base + '/' + filename_preferences)):
    sys.path.append(path_base)
else:
    setup_user_files(path_base)
    sys.path.append(path_base)

import plugins


def load_plugins():
    plugins_loaded = []
    for plugin in plugins.__all__:
        if plugin != '__init__':
            __import__('plugins.' + plugin)
            exec('plugins_loaded.append({"filename": "' + plugin + '.py", "plugin": plugins.' + plugin + '.extension()})')
    return plugins_loaded


class dmenu(object):

    path_base = os.path.expanduser('~') + '/.config/dmenu-extended'
    path_cache = path_base + '/cache.txt'
    path_preferences = path_base + '/' + filename_preferences
    path_configuration = path_base + '/' + filename_configuration

    dmenu_args = False
    bin_terminal = 'xterm'
    bin_filebrowser = 'xdg-open'
    bin_webbrowser = 'xdg-open'
    bin_fileopener = 'xdg-open'
    submenu_indicator = '* '
    filter_binaries = True

    plugins_loaded = False
    configuration = False
    preferences = False

    settings_loaded = False

    def __init__(self, arguments=[]):
        if arguments != []:
            self.dmenu_args = ['dmenu'] + arguments

    def get_plugins(self, force=False):

        if self.plugins_loaded == False:
            self.plugins_loaded = load_plugins()
        elif force:
            reload(plugins)
            self.plugins_loaded = load_plugins()

        return self.plugins_loaded

    def load_json(self, path):
        if os.path.exists(path):
            with open(path) as f:
                try:
                    return json.load(f)
                except:
                    print("Error parsing configuration from json file " + path)
                    return False
        else:
            print('Error opening json file ' + path)
            print('File does not exist')
            return False


    def save_json(self, path, items):
        with open(path, 'w') as f:
            json.dump(items, f, sort_keys=True, indent=4)


    def load_configuration(self):
        self.configuration = self.load_json(self.path_configuration)

        if self.configuration == False:
            self.open_file(path_base + '/' + filename_configuration)
            sys.exit()
        else:
            if 'dmenu_args' in self.configuration and self.dmenu_args == False:
                self.dmenu_args = ['dmenu'] + self.configuration['dmenu_args']
            if 'terminal' in self.configuration:
                self.bin_terminal = self.configuration['terminal']
            if 'filebrowser' in self.configuration:
                self.bin_filebrowser = self.configuration['filebrowser']
            if 'webbrowser' in self.configuration:
                self.bin_webbrowser = self.configuration['webbrowser']
            if 'fileopener' in self.configuration:
                self.bin_fileopener = self.configuration['fileopener']
            if 'submenu_indicator' in self.configuration:
                self.submenu_indicator = self.configuration['submenu_indicator']
            if 'filter_binaries' in self.configuration:
                self.filter_binaries = self.configuration['filter_binaries']


    def load_preferences(self):
        self.preferences = self.load_json(self.path_preferences)
        if self.preferences == False:
            self.open_file(path_base + '/' + filename_preferences)
            sys.exit()


    def load_settings(self):
        self.load_configuration()
        self.load_preferences()


    def connect_to(self, url):
        request = urllib2.Request(url)
        response = urllib2.urlopen(request)
        return response


    def download_text(self, url):
        return self.connect_to(url).readlines()


    def download_json(self, url):
        return json.load(self.connect_to(url))

    def message_open(self, message):
        self.message = subprocess.Popen(self.dmenu_args, stdin=subprocess.PIPE, preexec_fn=os.setsid)
        self.message.stdin.write(message)
        self.message.stdin.close()


    def message_close(self):
        os.killpg(self.message.pid, signal.SIGTERM)


    def menu(self, items, prompt=None):
        self.load_settings()
        params = []
        params += self.dmenu_args
        if prompt is not None:
            params += ["-p", prompt]
        p = subprocess.Popen(params, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        if type(items) == str:
            out = p.communicate(items)[0]
        else:
            out = p.communicate("\n".join(items))[0]

        if out.strip() == '':
            sys.exit()
        else:
            return out.strip('\n')


    def select(self, items, prompt=None, numeric=False):
        result = self.menu(items, prompt)
        for index, item in enumerate(items):
            if result.find(item) != -1:
                if numeric:
                    return index
                else:
                    return item
        return -1


    def sort_shortest(self, items):
        return sorted(items, cmp=lambda x, y: len(x) - len(y))


    def open_url(self, url):
        print('Opening url: "' + url + '" with ' + self.bin_webbrowser)
        os.system(self.bin_webbrowser + ' ' + url.replace(' ', '%20') + '&')


    def open_directory(self, path):
        print('Opening folder: "' + path + '" with ' + self.bin_filebrowser)
        os.system(self.bin_filebrowser + ' "' + path + '"')


    def open_terminal(self, command, hold=False, direct=False):
        if direct == False:
            mid = ' -e sh -c "'
        else:
            mid = ' '

        if hold:
            command += '; echo \'\nFinished!\n\nPress any key to close terminal\'; read var'
        
        full = self.bin_terminal + mid + command
        if direct == False:
            full += '"'
        print(full)
        os.system(full)


    def open_file(self, path):
        print('Opening file with command: ' + self.bin_fileopener + " '" + path + "'")
        os.system(self.bin_fileopener + " '" + path + "'")


    def execute(self, command, fork=None):
        if fork is not None:
            if fork == False:
                extra = ''
            else:
                extra = ' &'
        else:
            extra = ' &'
        os.system(command + extra)


    def cache_regenerate(self, debug=False, message=True):
        if message:
            self.message_open('Building cache...')
        self.load_settings()
        cache = self.cache_save(self.cache_build(debug))
        if message:
            self.message_close()
        return cache

    def cache_save(self, items):
        try:
            with open(self.path_cache, 'wb') as f:
                for item in items:
                    f.write(item+'\n')
            return 1
        except:
            import string
            tmp = []
            foundError = False
            for item in items:
                clean = True
                for char in item:
                    if char not in string.printable:
                        clean = False
                        foundError = True
                        # print('Non-printable characters detected in cache object: ')
                        # print('Remedy: ' + item)
                if clean:
                    tmp.append(item)
            if foundError:
                # print('Performance affected while these items remain')
                # print('This items have been excluded from cache')
                with open(self.path_cache, 'wb') as f:
                    for item in tmp:
                        f.write(item+'\n')
                return 2
            else:
                #print('Unknown error saving data cache')
                return 0

    def cache_open(self):
        try:
            with open(self.path_cache, 'rb') as f:
                return f.read()
        except:
            return False

    def cache_load(self):
        cache = self.cache_open()
        if cache == False:
            print('Cache was not loaded')
            if self.cache_regenerate() == False:
                self.menu(['Error caching data'])
                sys.exit()
            else:
                cache = self.cache_open()

        return cache

    def command_output(self, command):
        if type(command) == str:
            command = command.split(' ')
        handle = subprocess.Popen(command, stdout=subprocess.PIPE)
        return handle.communicate()[0].split('\n')


    def scan_binaries(self, filter_binaries=False):
        out = []
        for binary in self.command_output("ls /usr/bin"):
            if filter_binaries:
                if os.path.exists('/usr/share/applications/' + binary + '.desktop'):
                    if binary[:3] != 'gpk':
                        out.append(binary)
            else:
                out.append(binary)
        return out

    def cache_build(self, debug=False):
        print('')
        print('Starting to build the cache:')

        sys.stdout.write('Loading the list of valid file extensions...')
        sys.stdout.flush()
        valid_extensions = []
        if 'valid_extensions' in self.preferences:
            for extension in self.preferences['valid_extensions']:
                if extension[0] != '.':
                    extension = '.' + extension
                valid_extensions.append(extension.lower())
        print('Done!')

        if debug:
            print('Valid extensions:')
            sys.stdout.write('First 5 items: ')
            print(valid_extensions[:5])
            print(str(len(valid_extensions)) + ' loaded in total')
            print('')

        sys.stdout.write('Scanning user binaries...')
        filter_binaries = True
        try:
            if self.preferences['filter_binaries'] == False:
                filter_binaries = False
        except:
            pass

        binaries = self.scan_binaries(filter_binaries)
        print('Done!')

        if debug:
            print('Valid binaries:')
            sys.stdout.write('First 5 items: ')
            print(binaries[:5])
            print(str(len(binaries)) + ' loaded in total')
            print('')

        sys.stdout.write('Loading the list of indexed folders...')
        sys.stdout.flush()
        watch_folders = []
        if 'watch_folders' in self.preferences:
            watch_folders = self.preferences['watch_folders']
        watch_folders = map(lambda x: x.replace('~', os.path.expanduser('~')), watch_folders)
        print('Done!')

        if debug:
            print('Watch folders:')
            sys.stdout.write('First 5 items: ')
            print(watch_folders[:5])
            print(str(len(watch_folders)) + ' loaded in total')
            print('')

        sys.stdout.write('Loading the list of folders to be excluded from the index...')
        sys.stdout.flush()
        exclude_folders = []

        if 'exclude_folders' in self.preferences:
            for exclude_folder in self.preferences['exclude_folders']:
                exclude_folders.append(exclude_folder.replace('~', os.path.expanduser('~')))

        print('Done!')

        if debug:
            print('Excluded folders:')
            sys.stdout.write('First 5 items: ')
            print(exclude_folders[:5])
            print(str(len(exclude_folders)) + ' exclude_folders loaded in total')
            print('')

        filenames = []
        foldernames = []

        follow_simlinks = False
        try:
            if 'follow_simlinks' in self.preferences:
                follow_simlinks = self.preferences['follow_simlinks']
        except:
            pass

        if debug:
            if follow_simlinks:
                print('Indexing will not follow linked folders')
            else:
                print('Indexing will follow linked folders')

        sys.stdout.write('Scanning files and folders, this may take a while...')
        sys.stdout.flush()

        for watchdir in watch_folders:
            for root, dir , files in os.walk(watchdir, followlinks=follow_simlinks):
                if root.find('/.')  == -1:
                    for name in files:
                        if not name.startswith('.'):
                                if os.path.splitext(name)[1].lower() in valid_extensions:
                                    filenames.append(os.path.join(root,name))
                    for name in dir:
                        if not name.startswith('.'):
                            foldernames.append(os.path.join(root,name))

        foldernames = filter(lambda x: x not in exclude_folders, foldernames)

        print('Done!')

        if debug:
            print('Folders found:')
            sys.stdout.write('First 5 items: ')
            print(foldernames[:5])
            print(str(len(foldernames)) + ' found in total')
            print('')

            print('Files found:')
            sys.stdout.write('First 5 items: ')
            print(filenames[:5])
            print(str(len(filenames)) + ' found in total')
            print('')

        sys.stdout.write('Loading manually added items from user_preferences...')
        sys.stdout.flush()

        if 'include_items' in self.preferences:
            include_items = self.preferences['include_items']
        else:
            include_items = []
        print('Done!')

        if debug:
            print('Stored items:')
            sys.stdout.write('First 5 items: ')
            print(include_items[:5])
            print(str(len(include_items)) + ' items loaded in total')
            print('')

        sys.stdout.write('Loading available plugins...')
        sys.stdout.flush()

        plugins = self.get_plugins()
        plugin_titles = []
        for plugin in plugins:
            if hasattr(plugin['plugin'], 'is_submenu') and plugin['plugin'].is_submenu:
                plugin_titles.append(self.submenu_indicator + plugin['plugin'].title)
            else:
                plugin_titles.append(plugin['plugin'].title)
        print('Done!')

        if debug:
            print('Plugins loaded:')
            sys.stdout.write('First 5 items: ')
            print(plugin_titles[:5])
            print(str(len(plugin_titles)) + ' loaded in total')
            print('')

        sys.stdout.write('Ordering and combining results...')
        sys.stdout.flush()

        plugins = self.sort_shortest(plugin_titles)
        other = self.sort_shortest(include_items + binaries + foldernames + filenames)
        out = plugins

        out += other

        print('Done!')
        print('Cache building has finished.')
        print('')
        return out
