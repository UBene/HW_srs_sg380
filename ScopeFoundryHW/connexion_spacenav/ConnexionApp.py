'''
Connexion SpaceNavigator/SpaceMouse ScopeFoundry module
@author: Alan Buckley

Suggestions for improvement from Ed Barnard. <esbarnard@lbl.gov>

'''
import sys
from ScopeFoundry import BaseMicroscopeApp


class ConnexionApp(BaseMicroscopeApp):
	
	def setup(self):

		from ScopeFoundryHW.connexion_spacenav.connexion_hc import Connexion_HC
		self.connexion_hc = self.add_hardware(Connexion_HC(self))

		from ScopeFoundryHW.connexion_spacenav.connexion_mc import Connexion_MC
		self.connexion_mc = self.add_measurement(Connexion_MC(self))
		self.ui.show()
		self.ui.activateWindow()

		
if __name__ == '__main__':
	
	app = ConnexionApp(sys.argv)
	
	sys.exit(app.exec_())
	
