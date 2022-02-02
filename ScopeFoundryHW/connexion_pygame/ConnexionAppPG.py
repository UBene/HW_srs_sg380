'''
Connexion SpaceNavigator/SpaceMouse ScopeFoundry module
@author: Alan Buckley

Suggestions for improvement from Ed Barnard. <esbarnard@lbl.gov>

'''
import sys
from ScopeFoundry import BaseMicroscopeApp


class ConnexionAppPG(BaseMicroscopeApp):
	
	def setup(self):

		from ScopeFoundryHW.connexion_pygame.connexion_pg_hc import Connexion_pg_HC
		self.connexion_hc = self.add_hardware(Connexion_pg_HC(self))

		from ScopeFoundryHW.connexion_pygame.connexion_pg_mc import Connexion_pg_MC
		self.connexion_mc = self.add_measurement(Connexion_pg_MC(self))
		self.ui.show()
		self.ui.activateWindow()

		
if __name__ == '__main__':
	
	app = ConnexionAppPG(sys.argv)
	
	sys.exit(app.exec_())
	
