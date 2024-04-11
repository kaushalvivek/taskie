'''
The reporter service is responsible for generating the project report.
'''

class Reporter:
    def __init__(self):
        pass
    
    def trigger_report(self):
        raise NotImplementedError("Service not implemented yet")
    
    def _generate_report(self):
        raise NotImplementedError("Service not implemented yet")
    
    def _send_report(self):
        raise NotImplementedError("Service not implemented yet")