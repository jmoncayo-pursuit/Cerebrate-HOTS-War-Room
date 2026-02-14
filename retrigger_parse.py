
import os
import sys
from api.services.replay_service import ReplayService
from api.services.database import DatabaseManager

def retrigger(path):
    # Ensure we are in the right directory
    os.chdir("/Users/jmoncayopursuit.org/Desktop/Cerebrate-HOTS-War-Room")
    
    service = ReplayService()
    
    # Mock a file object
    class MockFile:
        def __init__(self, path):
            self.path = path
            self.filename = os.path.basename(path)
        def save(self, target):
            import shutil
            shutil.copy(self.path, target)
    
    mock_file = MockFile(path)
    result, code = service.process_replay_file(mock_file)
    print(f"Result: {result}")
    print(f"Code: {code}")

if __name__ == "__main__":
    path = "/Users/jmoncayopursuit.org/Library/Application Support/Blizzard/Heroes of the Storm/Accounts/474575/1-Hero-1-3446653/Replays/Multiplayer/2026-02-12 18.08.01 Hanamura Temple.StormReplay"
    retrigger(path)
