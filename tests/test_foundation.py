import os
os.environ['QT_QPA_PLATFORM'] = 'offscreen'
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from persistence import read_json, write_json
from state import PetState, Settings
from progression import Progression
from behavior import step_towards, turn_towards, edge_key

class LogicTests(unittest.TestCase):
    def test_movement_and_turning(self):
        self.assertEqual(step_towards(0,0,3,4,10),(3,4))
        self.assertEqual(step_towards(1,1,1,1,3),(1,1))
        self.assertAlmostEqual(turn_towards(179,-179,0.5),180)

    def test_atomic_save_and_invalid_data(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'pet_data.json'
            self.assertTrue(write_json(path, {'food': 200, 'energy': 'bad', 'happiness': -3}))
            self.assertEqual(PetState.load(path),PetState(100,75,0))
            path.write_text('[]')
            self.assertEqual(read_json(path),{})
            path.write_text('{broken')
            self.assertEqual(PetState.load(path),PetState())
            self.assertFalse(path.with_suffix('.tmp').exists())

    def test_progression_legacy_and_multiple_levels(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'progress.json'
            write_json(path,{'level':1,'xp':40})
            pet = Progression(path)
            self.assertTrue(pet.add_xp(100))
            self.assertEqual((pet.level,pet.xp),(3,15))
            self.assertEqual(Progression(path).xp,15)
            self.assertFalse(pet.add_xp(-1))

    def test_settings_and_needs(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'settings.json'
            write_json(path,{'animation_speed':900,'pet_visible':'false','web_visible':False})
            self.assertEqual(Settings.load(path),Settings(150,False,True))
            state=PetState(0,1,100)
            state.decay()
            self.assertEqual(state,PetState(0,0,99))
        self.assertEqual(edge_key({'name':'a'},{'name':'b'}),edge_key({'name':'b'},{'name':'a'}))

class QtTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from PySide6.QtWidgets import QApplication
        cls.app=QApplication.instance() or QApplication([])

    def test_overlay_panel_render_refresh_sleep(self):
        from main import Spider
        from pet_panel import PetPanel
        with tempfile.TemporaryDirectory() as folder, patch.dict(os.environ,LOCALAPPDATA=folder), patch('main.get_desktop_icons',return_value=[]):
            spider=Spider()
            spider.timer.stop()
            panel=PetPanel(spider)
            spider.pet_panel=panel
            panel.set_progression(spider.progression)
            panel.feed()
            self.assertEqual(spider.state.food,100)
            panel.pet_toggle.setChecked(False)
            self.assertFalse(spider.isVisible())
            panel.web_toggle.setChecked(False)
            self.assertFalse(spider.settings.web_visible)
            panel.sleep()
            for _ in range(400): spider.update_spider()
            self.assertFalse(spider.sleeping)
            self.assertGreaterEqual(spider.state.energy,60)
            a={'name':'a','x':50,'y':50};b={'name':'b','x':150,'y':150}
            spider.connect_web(a); spider.connect_web(b)
            self.assertEqual(len(spider.web_edges),1)
            spider.connect_web(a)
            self.assertEqual(len(spider.web_edges),1)
            with patch('main.get_desktop_icons',return_value=[a,b]): spider.refresh_environment()
            self.assertEqual(len(spider.web_edges),1)
            spider.settings.web_visible=True
            spider.home_icon=spider.desktop_icons[0]
            panel.show()
            self.app.processEvents()
            self.assertFalse(panel.grab().isNull())
            self.assertFalse(spider.grab().isNull())
            spider.refresh_environment()
            self.assertEqual(spider.web_edges,[])
            panel.close();spider.close()

if __name__=='__main__': unittest.main()
