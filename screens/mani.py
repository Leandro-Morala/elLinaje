from screens.basescreen import BaseScreen


class ManiScreen(BaseScreen):
    """Redirige al panel unificado de Colaboraciones."""

    def on_enter(self, *args):
        if self.manager and self.manager.has_screen('work'):
            self.manager.current = 'work'
