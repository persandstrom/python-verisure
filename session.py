I think that the connectionI of Verisure is not supported in Spain because it needs :https://mypages.verisure.com/ and this does not give supported in Spain.
Currently in Spain this website : https://customers.securitasdirect.es/ is used when logging.

Is possible change the next lines code in "session.py"?

DOMAIN = 'https://customers.securitasdirect.es/'
URL_LOGIN = DOMAIN + '/es/login/es'
URL_START = DOMAIN
RESPONSE_TIMEOUT = 10

thanks!
