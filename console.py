from ui import SearchIntent, EditorIntent
from clients import PlayerD, Backend
import playlist

class Console():

    def __init__(self, instance):
        self.instance = instance

    def execute(self, text):
        if text.startswith("!"):
            split = text[1:].split(" ")
            command = split[0]
            args = text[len(command)+1:]
            if command == 'pause':
                self.instance.player.pause()
            elif command == 'resume':
                self.instance.player.resume()
            elif command == 'go':
                if len(split) > 1:
                    self.instance.player.go_at(seconds=int(split[1]))
                else:
                    return 'Usage: !go {seconds}'
            elif command == 'volume':
                if len(split) > 1:
                    self.instance.player.set_volume(volume=int(split[1]))
                else:
                    return 'Usage: !voset_backend {ADDRESS}lume {0-150}'
            elif command == 'prefer_download':
                found = False
                if len(split) > 2:
                    if split[1] in self.instance.settings.providers:
                        self.instance.settings.providers[split[1]]['prefer_download'] = bool(split[2])
                        found = True
                    if not found:
                        return f'Backend not found. Backends: {self.instance.backend.providers}'
                else:
                    return 'Usage: !prefer_download {BACKEND} {True/False}'
            elif command == 'set_playerd':
                if len(split) > 1:
                    self.instance.player = PlayerD(split[1])
                else:
                    return 'Usage: !set_playerd {ADDRESS}'
            elif command == 'set_backend':
                if len(split) > 1:
                    self.instance.set_backend(Backend(split[1]))
                else:
                    return 'Usage: !set_backend {ADDRESS}'
            elif command == 'editor':
                return EditorIntent(self.instance)
            elif command == 'reload':
                self.instance.reload = True
                return "Reloading"
            elif command == 'playlist':
                if len(split) < 3:
                    return 'Usage: !playlist {play/add/remove} {NAME}'
                if split[1] == 'add':
                    self.instance.playlist.playlists.append(playlist.playlist(split[2]))
                self.instance.playlist.save()
            elif command in self.instance.backend.providers:
                res = self.instance.backend.search(provider=command, query=args)
                return SearchIntent(self.instance, res)
            else:
                return "Command not found"
        else:
            if self.instance.settings.collect_history:
                self.instance.settings.history.append(text)
                self.instance.settings.save()
            res = self.instance.backend.search_all(query=text, providers=self.instance.settings.global_search)
            return SearchIntent(self.instance, res)            
