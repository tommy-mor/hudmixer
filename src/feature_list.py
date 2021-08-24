from features import Feature


class Ammo(Feature):
    def gather(self):
        self.collect_file("resource/ui/hudammoweapons.res")
        self.hudlayout_grab('HudWeaponAmmo')


class Health(Feature):
    def gather(self):
        self.collect_file("resource/ui/hudplayerhealth.res")

        self.animation_grab('HudHealthBonusPulse')
        self.animation_grab('HudHealthBonusPulseLoop')
        self.animation_grab('HudHealthBonusPulseStop')
        self.animation_grab('HudHealthDyingPulse')
        self.animation_grab('HudHealthDyingPulseLoop')
        self.animation_grab('HudHealthDyingPulseStop')


class Scoreboard(Feature):
    def gather(self):
        self.collect_file("resource/ui/scoreboard.res")


class TargetId(Feature):
    def gather(self):
        self.collect_file("resource/ui/targetid.res")
        self.collect_file("resource/ui/spectatorguihealth.res")

        self.hudlayout_grab('CMainTargetID')
        self.hudlayout_grab('CSpectatorTargetID')
        self.hudlayout_grab('CSecondaryTargetID')
