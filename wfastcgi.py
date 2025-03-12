<?xml version="1.0" encoding="UTF-8"?>
<configuration>
    <system.webServer>
        <handlers>
            <add name="IEOWEB" path="*" verb="*" modules="FastCgiModule" scriptProcessor="C:\Users\IDEA\AppData\Local\Programs\Python\Python39\python.exe|C:\Users\IDEA\AppData\Local\Programs\Python\Python39\Lib\site-packages\wfastcgi.py" resourceType="Unspecified" requireAccess="Script" />
        </handlers>
    </system.webServer>
    <appSettings>
    <add key="WSGI_HANDLER" value="run.app" /> <!-- {name_of_file}.{name_of_flask_app}-->
    <add key="PYTHONPATH" value="C:\inetpub\wwwroot\IEO" />
  </appSettings>
</configuration>