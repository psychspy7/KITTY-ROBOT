import sys,time,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from brain import RobotBrain, point_to_rect_distance, ROBOT_R

class TestBrain(unittest.TestCase):
 def setUp(self):self.b=RobotBrain()
 def test_initial_state(self):
  s=self.b.snapshot();self.assertEqual(s['safety'],'READY');self.assertEqual(s['mode'],'IDLE');self.assertEqual(len(s['obstacles']),3)
 def test_goal_and_avoidance(self):
  self.assertIn('Route planned',self.b.action('go_to_zone',zone='presentation'))
  self.assertGreater(len(self.b.path),1)
  for n in range(6000):
   self.b.tick(.07)
   self.assertFalse(self.b._collides(self.b.pose.x,self.b.pose.y))
   if self.b.mode=='ARRIVED':break
  self.assertEqual(self.b.mode,'ARRIVED',self.b._mind_note(self.b._senses()))
 def test_no_route_target_inside_obstacle(self):
  self.assertIn('inside an obstacle',self.b.action('go_to',x=310,y=170))
  self.assertNotEqual(self.b.mode,'NAVIGATING')
 def test_estop_and_recovery(self):
  self.b.action('estop');p=(self.b.pose.x,self.b.pose.y)
  self.assertIn('rejected',self.b.action('forward'))
  for i in range(20):self.b.tick(.1)
  self.assertEqual((self.b.pose.x,self.b.pose.y),p)
  self.assertEqual(self.b.safety,'EMERGENCY STOP')
  self.b.action('reset_estop');self.assertEqual(self.b.safety,'READY')
 def test_manual_timeout(self):
  self.b.action('forward');self.assertEqual(self.b.mode,'MANUAL_FORWARD')
  self.b.manual_until=time.monotonic()-1
  self.b.tick(.1);self.assertEqual(self.b.mode,'IDLE')
 def test_obstacle_injection(self):
  self.assertIn('Obstacle placed',self.b.action('add_obstacle',x=405,y=440))
  self.assertEqual(len(self.b.obstacles),4)
 def test_chat_command(self):
  self.assertIn('Route planned',self.b.chat('go to the innovation lab'))
  self.assertIn('simulated',self.b.chat('what do you see?').lower())
  self.assertIn('Emergency stop activated',self.b.chat('emergency stop'))
  self.assertEqual(self.b.safety,'EMERGENCY STOP')

if __name__=='__main__':unittest.main()
