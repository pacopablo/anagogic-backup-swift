<!--<h2>Server Settings</h2>-->
<form class="form-horizontal" action="/save_settings" method="POST">
    <fieldset>
        <legend>Server Settings</legend>
        <div class="control-group">
            <label class="control-label">
                Dropbox
            </label>
            <div class="controls">
                <div class="btn-group">
                    %if not dropbox['appkey']:
                        <a class="btn btn-primary" href="#app_key_modal" role="button" data-toggle="modal">Set App Keys</a>
                    %else:
                        %if not dropbox['linked']:
                            <a class="btn btn-primary" href="{{dropbox['authorize']}}"
                                    ><i class="icon-user icon-white"></i> Link</a>
                        %else:
                            <a class="btn btn-primary" href="#"><i class="icon-user icon-white"></i> {{dropbox['account']['display_name']}}</a>
                            <a class="btn btn-primary dropdown-toggle" data-toggle="dropdown" href="#"><span class="caret"></span></a>
                            <ul class="dropdown-menu">
                                <li><a href="/unlink"><i class="icon-ban-circle"></i> Unlink</a></li>
                            </ul>
                        %end
                    %end
                </div>
            </div>
            <div id="app_key_modal" class="modal hide fade" role="dialog">
                <div class="modal-header">
                    <button type="button" class="close" data-dismiss="modal" aria-hidden="true">&times;</button>
                    <h3>Set Dropbox App Keys</h3>
                </div>
                <div class="modal-body">
                    <div class="control-group">
                        <label class="control-label" for="settings_app_key">
                            App Key:
                        </label>
                        <div class="controls">
                            <input type="text" class="input-medium" id="settings_app_key"
                                   name="app_key">
                        </div>
                    </div>
                    <div class="control-group">
                        <label class="control-label" for="settings_app_secret">
                            App Secret:
                        </label>
                        <div class="controls">
                            <input type="text" class="input-medium" id="settings_app_secret"
                                   name="app_secret">
                        </div>
                    </div>
                </div>
                <div class="modal-footer">
                    <a href="#" class="btn">Close</a>
<!--                    <div class="form-actions">
-->
                        <button type="submit" class="btn btn-primary">Save</button>
<!--                    </div>
-->
                </div>
            </div>
        </div>
        <div class="control-group">
            <label class="control-label" for="settings_hostname">
                Hostname:Port
            </label>
            <div class="controls">
                <input type="text" class="input-medium" id="settings_hostname"
                       name="settings_hostname"
                       value="{{data['hostname']}}:{{data['port']}}">
                <p>Hostname or IP address and port for the server</p>
            </div>
        </div>
        <div class="control-group">
            <label class="control-label" for="settings_appfolder">
                App Folder
            </label>
            <div class="controls">
                <input type="text" class="input-medium" id="settings_appfolder"
                       name="settings_appfolder"
                       value="{{data['appfolder']}}">
                <p>Folder in Dropbox under which all directories will be stored</p>
            </div>
        </div>
        <div class="control-group">
            <label class="control-label" for="settings_sentry">
                Sentry DSN
            </label>
            <div class="controls">
                <input type="text" class="input-medium" id="settings_sentry"
                       name="sentry_dsn"
                       value="{{data['sentrydsn']}}">
                <p>DSN of Sentry server for logging</p>
            </div>
            <label class="control-label" for="settings_sentrysite">
                Sentry Sitename
            </label>
            <div class="controls">
                <input type="text" class="input-medium" id="settings_sentrysite"
                       name="sentry_site"
                       value="{{data['sentrysite']}}">
                <p>Sitename to appear in Sentry logs</p>
            </div>
        </div>
        <div class="form-actions">
            <button type="submit" class="btn btn-primary">Update &raquo;</button>
        </div>
    </fieldset>
</form>
