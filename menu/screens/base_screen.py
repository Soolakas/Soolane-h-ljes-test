class BaseScreen:
    """Abstraktne baasklass kõigi menüüekraanide jaoks.
    Abstract base class for all menu screens."""

    def __init__(self, state_manager, settings):
        self.state_manager = state_manager  # Olekuhaldur, mis kontrollib ekraanivahetusi
        self.settings = settings            # Mängu seadete objekt

    def handle_events(self, events):
        """Töötleb sisendsündmused (hiirekliki jne). Tuleb alamklassis üle kirjutada."""
        raise NotImplementedError

    def update(self, dt):
        """Uuendab ekraani olekut. Vaikimisi ei tee midagi."""
        pass

    def draw(self, screen):
        """Joonistab ekraani sisu. Tuleb alamklassis üle kirjutada."""
        raise NotImplementedError

    def on_enter(self):
        """Kutsutakse välja, kui ekraan muutub aktiivseks."""
        pass

    def on_exit(self):
        """Kutsutakse välja, kui ekraan kaotab aktiivsuse."""
        pass
