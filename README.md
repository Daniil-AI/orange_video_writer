# Работа скрипта

Скрипт работает с двумя классами каждый из которых имеет свой поток
* Display получает доступ к камере в capture_thread и если запушен display_thread выводит изображение на 0 дисплей в системе
* VideoRecorder создает обьект видеоролика и получает массив кадров и в video_thread получает кадры от класса Display которые помещаются в ролик

При каждом запуске на рабочем столе создается папка с текущей датой в которой будут размешены ролики

## Первые шаги
Посмотреть что orangepi видит камеру
```ls -l /dev/video*```

Проверить формат работы камеры командой
```v4l2-ctl --device=/dev/video0 --list-formats-ext```

Через терминал вызвать простую команду захваты камеры пример для разрешения 1920х1080
```gst-launch-1.0 v4l2src device=/dev/video0 ! image/jpeg, width=1920, height=1080, framerate=30/1 ! jpegdec ! videoconvert ! autovideosink```

Если этот этап не вызвал конфликтов работе железа то можно двигаться дальше 


## Установка GStreamer

Вызываем python
```python3```

Вводим такой код
```
import cv2
print(cv2.getBuildInformation())
```
 
Если видим что GStreamer не установлен то докачиваем его переустановкой opencv
GStreamer:                   NO

### Код установки

Клонируем репозитории OpenCV и дополнительных модулей
```
git clone https://github.com/opencv/opencv.git
git clone https://github.com/opencv/opencv_contrib.git
```

Переходим в директорию OpenCV
```
cd opencv
mkdir build
cd build
```

Запускаем CMake с указанием дополнительных модулей и GStreamer
```
cmake -D CMAKE_BUILD_TYPE=Release \
      -D CMAKE_INSTALL_PREFIX=/usr/local \
      -D OPENCV_EXTRA_MODULES_PATH=../../opencv_contrib/modules \
      -D WITH_GSTREAMER=ON \
      -D BUILD_opencv_python3=ON \
      ..
```

Компиляция (может занять продолжительное время)
```
make -j4
```

Установка
```
sudo make install
sudo ldconfig
```

### Дополнительные шаги

После перекомпиляции OpenCV вызов python-команды:
```
print(cv2.getBuildInformation())
```

Напротив GStreamer будет стоять его актвльная версия, если это не так то возможно имеет добавить в .bashrc следующий экспорт
```
export PYTHONPATH=$PYTHONPATH:/usr/local/lib/python3.9/site-packages/cv2/python-3.9/
```


## Чтобы код работал 

достатоно запустить команду

```crontab -e```

и в ней указать путь до файла автозапуска

```@reboot ~/Desktop/orange_video_writer/auto_start.sh```

### Дополнительно
Скрипт сам активирует виратуальную среду которая идет в коплекте с репозиторием, однако если с ее запуском возникнут пробелмы можно установить пакеты зависимостей самостоятельно
