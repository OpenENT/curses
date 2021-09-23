from ui import ExceptionIntent, SearchIntent, PlaylistIntent, EditorIntent
from clients import PlayerD, Backend
from traceback import format_exc

import playlist

class Command():

    def __init__(self, name):
        self.name = name

    def execute(self, instance, split, args):
        pass

class PauseCommand(Command):

    def __init__(self):
        super().__init__('pause')

    def execute(self, instance, split, args):
        instance.player.pause()

class ResumeCommand(Command):

    def __init__(self):
        super().__init__('resume')

    def execute(self, instance, split, args):
        instance.player.resume()

class GoCommand(Command):

    def __init__(self):
        super().__init__('go')

    def execute(self, instance, split, args):
        if len(split) > 1:
            instance.player.go_at(seconds=int(split[1]))
        else:
            return 'Usage: !go {seconds}'

class VolumeCommand(Command):

    def __init__(self):
        super().__init__('volume')

    def execute(self, instance, split, args):
        if len(split) > 1:
            instance.player.set_volume(volume=int(split[1]))
        else:
            return 'Usage: !volume {0-150}'

class PreferCommand(Command):

    def __init__(self):
        super().__init__('prefer_download')

    def execute(self, instance, split, args):
        found = False
        if len(split) > 2:
            if split[1] in instance.settings.providers:
                instance.settings.providers[split[1]]['prefer_download'] = bool(split[2])
                found = True
            if not found:
                return f'Backend not found. Backends: {instance.backend.providers}'
        else:
            return 'Usage: !prefer_download {BACKEND} {True/False}'

class PlayerDCommand(Command):

    def __init__(self):
        super().__init__('set_playerd')

    def execute(self, instance, split, args):
        if len(split) > 1:
            instance.player = PlayerD(split[1])
        else:
            return 'Usage: !set_playerd {ADDRESS}'

class BackendCommand(Command):

    def __init__(self):
        super().__init__('set_backend')

    def execute(self, instance, split, args):
        if len(split) > 1:
            instance.set_backend(Backend(split[1]))
        else:
            return 'Usage: !set_backend {ADDRESS}'

class EditorCommand(Command):

    def __init__(self):
        super().__init__('editor')

    def execute(self, instance, split, args):
        return EditorIntent(instance)

class ReloadCommand(Command):

    def __init__(self):
        super().__init__('reload')

    def execute(self, instance, split, args):
        instance.reload = True

class PlaylistCommand(Command):

    def __init__(self):
        super().__init__('playlist')

    def execute(self, instance, split, args):
        if len(split) < 3:
            return 'Usage: !playlist {play/add/remove} {NAME}'
        name = args[len(split[1]) + 1:]
        if split[1] == 'add':
            instance.playlist.playlists.append(playlist.playlist(name))
        plist = None
        for pl in instance.playlist.playlists:
            if name in pl['name']:
                plist = pl
                if split[1] == 'remove':
                    instance.playlist.playlists.remove(plist) # TODO: del file
                elif split[1] == 'play':
                    instance.player.play_playlist(plist)
                elif split[1] == 'show':
                    return PlaylistIntent(instance, plist)
                instance.playlist.save()

class CharCommand(Command):

    def __init__(self):
        super().__init__('char')

    def execute(self, instance, split, args):
        if len(split) > 1:
            return f'{ord(args[0])}'
        else:
            return 'Usage: !char character'

class Console():

    def __init__(self, instance):
        self.instance = instance
        self.commands = [
            PauseCommand(), ResumeCommand(), GoCommand(), 
            VolumeCommand(), PreferCommand(), PlayerDCommand(), BackendCommand(),
            EditorCommand(), ReloadCommand(), PlaylistCommand(), CharCommand()
            ]

    def execute(self, text):
        if text.startswith("!"):
            split = text[1:].split(" ")
            command = split[0]
            args = text[len(command)+2:]
            if command in self.instance.backend.providers:
                try:
                    res = self.instance.backend.search(provider=command, query=args)
                    return SearchIntent(self.instance, res)
                except Exception as e:
                    return ExceptionIntent(self.instance, e, format_exc())
            else:
                for cmd in self.commands:
                    if command == cmd.name:
                        try:
                            return cmd.execute(self.instance, split, args)
                        except Exception as e:
                            return ExceptionIntent(self.instance, e, format_exc())
        else:
            try:
                if self.instance.settings.collect_history:
                    self.instance.settings.insert_history(text)
                if self.instance.cache.get_cache('search', text) is not None:
                    res = self.instance.cache.get_cache('search', text)['res']
                else:
                    res = self.instance.backend.search_all(query=text, providers=self.instance.settings.global_search)
                    if self.instance.settings.collect_cache:
                        self.instance.cache.put_cache('search', text, {'res': res})
                return SearchIntent(self.instance, res)            
            except Exception as e:
                return ExceptionIntent(self.instance, e, format_exc())
