from servers.models import Server

def list_servers(request):
    servers = Server.objects.all().order_by('server_name')
    return {'list_all_servers': servers}