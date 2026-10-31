# Лабораторная работа №4


**Студент:** Bolgari Ivan   
**Группа:** I-2402
------------------------------------------------------------------------

## 1. Описание проекта

Цель лабораторной работы --- изучить настройку Jenkins для автоматизации
задач DevOps, научиться запускать Jenkins Controller и отдельный SSH
Agent в Docker-контейнерах, подключать агент к контроллеру и создавать
Pipeline для автоматического выполнения этапов PHP-проекта.


Используемая архитектура состоит из двух основных компонентов:

-   **Jenkins Controller** --- центральный сервер Jenkins. Через
    веб-интерфейс он управляет заданиями, Pipeline, узлами и
    результатами сборок.
-   **SSH Agent** --- отдельный Docker-контейнер, на котором Jenkins
    может выполнять команды сборки и тестирования. Для подключения
    используется SSH-аутентификация.

Контейнеры взаимодействуют через общую Docker bridge-сеть
`jenkins-network`. Данные Jenkins сохраняются в Docker volume
`jenkins_home`, поэтому настройки не теряются при обычном перезапуске
контейнера.

### Структура каталога

``` text
lab04/
├── docker-compose.yml
├── Dockerfile
├── .env                  # локальный файл, не загружается в GitHub
├── .gitignore
├── secrets/              # SSH-ключи, не загружаются в GitHub
└── readme.md
```

**Рисунок 1 --- Структура каталога `lab04`**![alt text](<lab4/Снимок экрана от 2026-11-01 00-14-12.png>)


------------------------------------------------------------------------

## 2. Шаги по настройке Jenkins Controller

### 2.1. Подготовка окружения

Перед началом работы были проверены установленные инструменты:

``` bash
docker --version
docker compose version
git --version
```

Также была проверена работа службы Docker:

``` bash
sudo systemctl status docker
```

При необходимости Docker запускался командами:

``` bash
sudo systemctl start docker
sudo systemctl enable docker
```

### 2.2. Конфигурация Docker Compose

В `docker-compose.yml` был описан сервис `jenkins-controller`:

``` yaml
services:
  jenkins-controller:
    image: jenkins/jenkins:lts
    container_name: jenkins-controller
    restart: unless-stopped
    ports:
      - "8080:8080"
      - "50000:50000"
    volumes:
      - jenkins_home:/var/jenkins_home
    networks:
      - jenkins-network
```

Назначение основных параметров:

-   `image` --- официальный LTS-образ Jenkins.
-   `ports` --- публикация веб-интерфейса на порту `8080` и порта
    `50000`, используемого некоторыми способами подключения агентов.
-   `volumes` --- сохранение данных Jenkins в постоянном Docker volume.
-   `networks` --- подключение контейнера к общей сети.
-   `restart: unless-stopped` --- автоматический перезапуск контейнера
    после сбоя или перезагрузки Docker, если он не был остановлен
    вручную.

Для запуска и проверки контейнеров использовались команды:

``` bash
sudo docker compose up -d
sudo docker compose ps
```

Веб-интерфейс Jenkins открывался по адресу:

``` text
http://localhost:8080
```

### 2.3. Первоначальная настройка Jenkins

Для получения первоначального пароля администратора использовалась
команда:

``` bash
sudo docker exec jenkins-controller \
  cat /var/jenkins_home/secrets/initialAdminPassword
```

После входа в веб-интерфейс были выполнены следующие действия:

1.  Выбрана установка рекомендованных плагинов (**Install suggested
    plugins**).
2.  Создан пользователь администратора.
3.  Проверен адрес Jenkins.
4.  Открыт раздел управления Jenkins.

**Рисунок 2 --- Веб-интерфейс Jenkins после первоначальной настройки**![alt text](<lab4/Снимок экрана от 2026-11-01 00-16-19.png>)


**Рисунок 3 --- Контейнер Jenkins Controller**
![alt text](<lab4/Снимок экрана от 2026-11-01 00-15-42.png>)

------------------------------------------------------------------------

## 3. Шаги по настройке SSH-агента

### 3.1. Создание SSH-ключей

Для аутентификации Jenkins Controller на SSH Agent была создана пара
SSH-ключей. Приватный ключ хранится локально и добавляется в Jenkins
Credentials, а публичный ключ передаётся контейнеру агента.

В ходе настройки для совместимости с SSH-библиотекой Jenkins был создан
RSA-ключ в PEM-формате:

``` bash
ssh-keygen -t rsa -b 4096 -m PEM \
  -f secrets/jenkins_agent_rsa -N ""
```

Файлы:

-   `secrets/jenkins_agent_rsa` --- приватный ключ;
-   `secrets/jenkins_agent_rsa.pub` --- публичный ключ.

Приватный ключ нельзя публиковать или отправлять в GitHub.

### 3.2. Создание Dockerfile

Для SSH Agent был подготовлен `Dockerfile`:

``` dockerfile
FROM jenkins/ssh-agent

USER root

RUN apt-get update && apt-get install -y php-cli \
    && rm -rf /var/lib/apt/lists/*
```

Используется официальный образ `jenkins/ssh-agent`. Дополнительно
устанавливается PHP CLI, чтобы агент мог выполнять PHP-команды и тесты.

### 3.3. Передача публичного ключа контейнеру

Публичный ключ был записан в `.env`:

``` bash
echo "JENKINS_AGENT_SSH_PUBKEY=$(cat secrets/jenkins_agent_rsa.pub)" > .env
```


### 3.4. Конфигурация SSH Agent в Docker Compose

В `docker-compose.yml` был добавлен сервис:

``` yaml
  ssh-agent:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: ssh-agent
    restart: unless-stopped
    environment:
      - JENKINS_AGENT_SSH_PUBKEY=${JENKINS_AGENT_SSH_PUBKEY}
    volumes:
      - jenkins_agent_volume:/home/jenkins/agent
    depends_on:
      - jenkins-controller
    networks:
      - jenkins-network
```

Оба сервиса подключены к сети `jenkins-network`. Благодаря Docker DNS
контроллер обращается к агенту по имени сервиса `ssh-agent`, используя
порт `22`.

Для применения конфигурации использовались команды:

``` bash
sudo docker compose --env-file .env up -d --build
sudo docker compose ps
```

Для просмотра журнала агента:

``` bash
sudo docker logs ssh-agent --tail=50
```

**Рисунок 5 --- Работающие Docker-контейнеры**![alt text](<lab4/Снимок экрана от 2026-11-01 00-15-42.png>)


### 3.5. Добавление SSH Credentials в Jenkins


Были указаны следующие параметры:

  Поле          Значение
  ------------- ------------------------------------------------
  Kind          SSH Username with private key
  Scope         Global
  ID            `jenkins-agent-key`
  Username      `jenkins`
  Private Key   Enter directly
  Passphrase    Пусто, так как ключ создан без парольной фразы

В поле Private Key было вставлено содержимое файла
`secrets/jenkins_agent_rsa`, то есть приватный ключ, а не файл с
расширением `.pub`.

### 3.6. Создание узла SSH Agent

В Jenkins был создан постоянный узел 

Параметры узла:

  -----------------------------------------------------------------------
  Поле                                Значение
  ----------------------------------- -----------------------------------
  Node name                           `ssh-agent1`

  Type                                Permanent Agent

  Number of executors                 `2`

  Remote root directory               `/home/jenkins/agent`

  Labels                              `php-agent`

  Usage                               Only build jobs with label
                                      expressions

  Launch method                       Launch agents via SSH

  Host                                `ssh-agent`

  Credentials                         `jenkins-agent-key`

  Host Key Verification Strategy      Non verifying Verification Strategy
                                      

  Availability                        Keep this agent online as much as
                                      possible
  -----------------------------------------------------------------------



**Рисунок 6 --- SSH Credentials в Jenkins**

![alt text](<lab4/Снимок экрана от 2026-11-01 00-24-19.png>)


**Рисунок 8 --- SSH Agent в состоянии Online**
![alt text](<lab4/Снимок экрана от 2026-11-01 00-16-10.png>)


------------------------------------------------------------------------

## 4. Шаги по созданию и настройке конвейера Jenkins

### 4.1. Подготовка PHP-проекта

Для выполнения задания требуется PHP-проект в GitHub, содержащий
исходный код и unit-тесты. Если проект использует Composer и PHPUnit, в
его корне должны находиться `composer.json` и каталог с тестами,
например `tests/`.


### 4.2. Создание Jenkinsfile

В корне PHP-репозитория создаётся файл `Jenkinsfile`. Пример Pipeline
для проекта с Composer и PHPUnit:

``` groovy
pipeline {
    agent {
        label 'php-agent'
    }

    stages {
        stage('Install Dependencies') {
            steps {
                echo 'Preparing project...'
                sh 'php --version'
                sh 'composer install --no-interaction'
            }
        }

        stage('Test') {
            steps {
                echo 'Running tests...'
                sh 'composer test'
            }
        }
    }

    post {
        always {
            echo 'Pipeline completed.'
        }
        success {
            echo 'All stages completed successfully!'
        }
        failure {
            echo 'Errors detected in the pipeline.'
        }
    }
}
```

Команда `composer test` должна быть определена в секции `scripts` файла
`composer.json`, например:

``` json
{
    "scripts": {
        "test": "phpunit tests"
    }
}
```

Команды в Pipeline необходимо адаптировать к конкретному PHP-проекту.
Если проект не использует Composer или PHPUnit, следует указать
фактическую команду запуска его тестов.

### 4.3. Создание Pipeline в Jenkins

В Jenkins выбирается **New Item**, вводится имя Pipeline, например
`PHP-CI-Pipeline`, и выбирается тип **Pipeline**.

В настройках Pipeline указывается:

  Поле               Значение
  ------------------ -------------------------------------------
  Definition         Pipeline script from SCM
  SCM                Git
  Repository URL     URL PHP-репозитория на GitHub
  Branch Specifier   `*/main` (или фактическая основная ветка)
  Script Path        `Jenkinsfile`

После сохранения задания нажимается **Build Now**.

---------------------------------------------

## 5. Ответы на контрольные вопросы

### 5.1. Каковы преимущества использования Jenkins для автоматизации задач DevOps?

Jenkins --- это сервер автоматизации с открытым исходным кодом. Он
позволяет автоматизировать сборку, тестирование и другие этапы
разработки программного обеспечения.

Основные преимущества:

1.  **Автоматизация повторяющихся задач.** Сборку и тестирование не
    нужно каждый раз запускать вручную.
2.  **Интеграция с Git.** Jenkins может получать исходный код из GitHub
    и запускать Pipeline при изменениях в репозитории.
3.  **Раннее обнаружение ошибок.** Автоматические тесты помогают
    находить проблемы до того, как изменения попадут в основную версию
    проекта.
4.  **Гибкость.** Pipeline можно описывать в `Jenkinsfile` с помощью
    Groovy-синтаксиса и разделять на отдельные этапы.
5.  **Масштабируемость.** Controller может распределять задачи между
    несколькими агентами.
6.  **Большая экосистема плагинов.** Плагины позволяют интегрировать
    Jenkins с GitHub, Docker, системами тестирования, уведомлениями и
    другими инструментами.
7.  **Прозрачность процесса.** В Jenkins можно просматривать историю
    сборок, журналы и результаты выполнения задач.

### 5.2. Какие ещё существуют агенты Jenkins?

В Jenkins агенты --- это узлы, на которых выполняются задания,
назначенные контроллером. Они могут работать в разных операционных
системах и средах.

Примеры агентов:

-   **Linux Agent** --- выполняет команды и сборки в Linux.
-   **Windows Agent** --- подходит для сборки и тестирования приложений
    под Windows.
-   **macOS Agent** --- используется для разработки и тестирования
    приложений для macOS и iOS.
-   **Docker Agent** --- запускает сборки в изолированных
    Docker-контейнерах.
-   **Kubernetes Agent** --- позволяет динамически создавать агенты в
    Kubernetes для выполнения заданий.
-   **Inbound Agent** --- самостоятельно подключается к Jenkins
    Controller, что удобно, если контроллер не может напрямую
    подключиться к агенту.
-   **SSH Agent** --- подключается к контроллеру через SSH. Такой
    вариант был настроен в данной лабораторной работе.

Агенты могут отличаться не только операционной системой, но и способом
подключения, доступными инструментами и назначением.

### 5.3. С какими проблемами вы столкнулись при настройке Jenkins и как вы их решили?

В процессе настройки возникли следующие проблемы:

**1. Контейнеры не запускались автоматически после перезагрузки
Ubuntu.**

Для решения была проверена служба Docker и добавлена политика
перезапуска:

``` yaml
restart: unless-stopped
```

После этого контейнеры можно запускать командой:

``` bash
sudo docker compose up -d
```

**2. Jenkins не мог разрешить имя SSH Agent.**

Появлялась ошибка:

``` text
Temporary failure in name resolution
```

Была проверена общая Docker-сеть. Оба контейнера должны находиться в
одной сети `jenkins-network`, чтобы контроллер мог обращаться к агенту
по имени `ssh-agent`.

**3. Jenkins не принимал первоначальный SSH-ключ.**

В журнале появилась ошибка:

``` text
PEM problem: it is of unknown type.
```

Причина --- несовместимость формата первоначального Ed25519-ключа с
используемой SSH-библиотекой Jenkins. Для решения был создан RSA-ключ в
PEM-формате:

``` bash
ssh-keygen -t rsa -b 4096 -m PEM \
  -f secrets/jenkins_agent_rsa -N ""
```

Затем публичный ключ был передан контейнеру, а соответствующий приватный
ключ добавлен в Jenkins Credentials.


------------------------------------------------------------------------

## 6. Заключение

В ходе лабораторной работы была изучена настройка Jenkins для
автоматизации DevOps-задач. Были рассмотрены Controller и Agent, создана
Docker-инфраструктура с двумя контейнерами, настроена SSH-аутентификация
и подготовлен постоянный узел с меткой `php-agent`.

Также была изучена структура Jenkins Pipeline и подготовлен пример
конвейера, включающего установку зависимостей и выполнение unit-тестов
PHP-проекта.

