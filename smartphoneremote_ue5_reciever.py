import preference, arcore, argparse

recieverCLIParser = argparse.ArgumentParser(description = 'Smartphone Remote middleman for UE5.')
recieverCLIParser.add_argument(
    '--bind', '-b', 
    required = False,
    type = int, 
    dest = 'recieverCLIArgs_bindPort',
    help = 'the port where the reciever will listen for incoming connections (always listens on 0.0.0.0) (default: 8096)',
)
recieverCLIParser.add_argument(
    '--generate-qr-code', '-g',
    required = False,
    type = str,
    dest = 'recieverCLIArgs_generateQRCode',
    help = '(yes/no) whether or not the program should generate a QR code for easy connections (default: no)'
)