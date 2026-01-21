from users.infrastructure.models import Usuario


class CrearUsuarioUseCase:

    def __init__(self, usuario_repository):
        self.usuario_repository = usuario_repository

    def execute(self, data):
        usuario = Usuario(
            nombre=data.nombre,
            apellido=data.apellido,
            email=data.email,
            password=data.password,
            id_rol=data.id_rol,
            estado="Activo"
        )
        return self.usuario_repository.create(usuario)
