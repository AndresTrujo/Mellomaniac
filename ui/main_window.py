from PySide6.QtWidgets import (
    QWidget,
    QMainWindow,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QSlider,
    QFileDialog,
    QPushButton,
)
from PySide6.QtCore import Qt, QUrl, QByteArray
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput, QMediaMetaData
from PySide6.QtGui import QPixmap, QImage
import json
from pathlib import Path




class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        WINDOW_X = 100
        WINDOW_Y = 100
        WINDOW_WIDTH = 600
        WINDOW_HEIGHT = 800
        self.media_player = QMediaPlayer()
        self.music_files_paths = []
        self.audio_output = QAudioOutput()
        self.song_progress = QSlider(Qt.Orientation.Horizontal)
        self.music_list = QListWidget() # Lista de canciones disponibles
        self.toggle_media_button = QPushButton("Stop Music") # boton de pausa/reproducir
        self.song_name = QLabel(wordWrap=True, text="Start playing some music...")
        self.time_passed = QLabel(text="0:00")
        self.time_total = QLabel(text="0:00")
        self.album_cover = QLabel()
        self.select_directory_button = None  # Añadimos una referencia al botón
        central_widget = QWidget()  # Widget vacio que actua como base de la ventana
        lower_info_layout = QHBoxLayout()  # QH PARA LA BARRA DE PROGRESO y la duracion, se une a upper info.
        app_layout = QHBoxLayout() #Contendra dos sub-layouts
        sidebar_layout = QVBoxLayout() # controles de reproduccion, volumen, Datos, Queue
        content_layout = QVBoxLayout() # Este layout contendra todo lo que estaba en main_layout
        config_file = Path("config.json")

        self.setWindowTitle("Mellomaniac — Music Player")  # Music Player string should change for the current song's name
        self.setGeometry(WINDOW_X, WINDOW_Y, WINDOW_WIDTH, WINDOW_HEIGHT)

        central_widget.setLayout(app_layout)
        self.setCentralWidget(central_widget)
        self.song_name.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        lower_info_layout.addWidget(self.time_passed)
        lower_info_layout.addWidget(self.song_progress)
        lower_info_layout.addWidget(self.time_total)
        content_layout.addLayout(lower_info_layout)
        content_layout.addWidget(self.music_list)
        sidebar_layout.addWidget(self.album_cover)
        sidebar_layout.addWidget(self.song_name)
        sidebar_layout.addWidget(self.toggle_media_button)
        app_layout.addLayout(sidebar_layout)
        app_layout.addLayout(content_layout)

        if not config_file.exists():
            self.select_directory_button = QPushButton("Selecciona tu directorio de musica...")
            content_layout.addWidget(self.select_directory_button)
            self.select_directory_button.clicked.connect(self.select_music_directory)
        else:
            music_path = self.get_music_path()
            self.load_music(music_path)

        self.music_list.itemClicked.connect(self.play_song)
        self.toggle_media_button.clicked.connect(self.toggle_play_pause)
        self.media_player.playbackStateChanged.connect(self.update_play_button)
        self.media_player.durationChanged.connect(self.update_duration)
        self.media_player.positionChanged.connect(self.update_progress)
        self.media_player.mediaStatusChanged.connect(self.update_metadata)
        self.song_progress.sliderMoved.connect(self.change_position)
        
        #Fin de __init__()


    def update_metadata(self, status: QMediaPlayer.MediaStatus) -> None:
        if status == QMediaPlayer.MediaStatus.LoadedMedia:
            # Obtener el objeto de metadatos
            metadata = self.media_player.metaData()
            self.song_name.setText(metadata.value(QMediaMetaData.Key.Title))
            # Intentar obtener la imagen directamente
            cover_art_image = metadata.value(QMediaMetaData.Key.CoverArtImage)
            
            if cover_art_image and isinstance(cover_art_image, QImage):
                pixmap = QPixmap.fromImage(cover_art_image)
                self.album_cover.setPixmap(
                    pixmap.scaled(
                        self.album_cover.size(),
                        aspectMode=Qt.AspectRatioMode.KeepAspectRatio,
                        mode=Qt.TransformationMode.SmoothTransformation
                    )
                )
                print("Portada de álbum encontrada y mostrada.")
                return
            
    def select_music_directory(self) -> None: # Slot para seleccionar el directorio de musica
        music_directory = QFileDialog.getExistingDirectory()
        if music_directory:
            with open("config.json","w") as config_json:
                json.dump({"music_path":music_directory}, config_json)
                
            music_path = self.get_music_path()
            self.load_music(music_path)

            if self.select_directory_button:
                self.select_directory_button.hide()
                self.select_directory_button.deleteLater()
                
    def load_music(self, music_path: Path) -> None:
        supported_suffixes = [".mp3", ".wav", ".ogg", ".FLAC"]
        for item in music_path.rglob("*"):
            if item.suffix in supported_suffixes:
                self.music_files_paths.append(item)
                self.music_list.addItem(item.name)

    def play_song(self, song: QListWidgetItem):
        song_path = self.music_files_paths[self.music_list.row(song)]
        song_url = QUrl.fromLocalFile(str(song_path))
        self.media_player.setSource(song_url)
        self.media_player.setAudioOutput(self.audio_output)
        self.media_player.play()

    def get_music_path(self) -> Path:
        with open("config.json", "r") as config_json:
            json_dict = json.load(config_json)
            music_path = Path(json_dict["music_path"])
            return music_path

    def toggle_play_pause(self) -> None:
        if self.media_player.isPlaying():
            self.media_player.pause()
        else:
            self.media_player.play()

    def update_play_button(self, playback_state: QMediaPlayer.PlaybackState) -> None:
        if playback_state == QMediaPlayer.PlaybackState.PlayingState:
            self.toggle_media_button.setText("Pause Music")
        elif (
            playback_state == QMediaPlayer.PlaybackState.PausedState
            or playback_state == QMediaPlayer.PlaybackState.StoppedState
        ):
            self.toggle_media_button.setText("Play Music")

    def update_duration(self, duration: int) -> None:
        self.song_progress.setMaximum(duration)
        self.time_total.setText(self.mills_to_mmss(duration))

    def mills_to_mmss(self, duration: int) -> str:
        total_seconds = duration // 1000
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        return f"{minutes:02}:{seconds:02}"

    def update_progress(self, position: int) -> None:
        self.time_passed.setText(self.mills_to_mmss(position))
        self.song_progress.setSliderPosition(position)

    def change_position(self, position: int) -> None:
        self.media_player.setPosition(position)


#TODO: Load song cover from metadata