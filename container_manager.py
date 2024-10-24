import subprocess

class ContainerManager:
    def __init__(self, containers):
        self.containers = containers

    def restart_containers(self):
        for container in self.containers:
            try:
                print(f"Перезагружаем контейнер: {container}")
                subprocess.run(["docker", "restart", container], check=True)
                print(f"Контейнер {container} успешно перезагружен.")
            except subprocess.CalledProcessError as e:
                print(f"Ошибка при перезагрузке контейнера {container}: {e}")
