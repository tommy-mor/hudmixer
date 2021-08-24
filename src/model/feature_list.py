from features import Feature


class Ammo(Feature):
    def gather(self):
        self.collect_file("resource/ui/hudammoweapons.res")
        self.hudlayout_grab('HudWeaponAmmo')

        self.animation_grab('HudLowAmmoPulse')
        self.animation_grab('HudLowAmmoPulseLoop')
        self.animation_grab('HudLowAmmoPulseStop')


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
        self.collect_file("resource/ui/healthiconpanel.res")

        self.hudlayout_grab('CMainTargetID')
        self.hudlayout_grab('CSpectatorTargetID')
        self.hudlayout_grab('CSecondaryTargetID')


class MedicCharge(Feature):
    def gather(self):
        self.collect_file('resource/ui/hudmediccharge.res')
        self.hudlayout_grab('HudMedicCharge')

        self.animation_grab('HudMedicCharged')
        self.animation_grab('HudMedicChargedLoop')
        self.animation_grab('HudMedicChargedStop')


classes = [Ammo, Health, Scoreboard, TargetId, MedicCharge]
