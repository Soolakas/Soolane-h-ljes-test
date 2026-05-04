class BaseScreen:
    """Abstract base class for all menu screens."""

    def __init__(self, state_manager, settings):
        self.state_manager = state_manager
        self.settings = settings

    def handle_events(self, events):
        raise NotImplementedError

    def update(self, dt):
        pass

    def draw(self, screen):
        raise NotImplementedError

    def on_enter(self):
        pass

    def on_exit(self):
        pass
