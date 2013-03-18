<!--<h2>Server Settings</h2>-->
<form class="form-horizontal" action="/save_settings" method="POST">
    <fieldset>
        <legend>Server Settings</legend>
        <div class="control-group">
            <label class="control-label" for="settings_swift_account">
                Swift Account
            </label>
            <div class="controls">
                <input type="text" class="input-medium" id="settings_swift_account"
                       name="settings_swift_account"
                       value="{{data['swift_account']}}">
            </div>
            <label class="control-label" for="settings_swift_password">
                Swift Password
            </label>
            <div class="controls">
                <input type="text" class="input-medium" id="settings_swift_password"
                       name="settings_swift_password"
                       value="{{data['swift_password']}}">
            </div>
            <label class="control-label" for="settings_swift_key">
                Swift Key
            </label>
            <div class="controls">
                <input type="text" class="input-medium" id="settings_swift_key"
                       name="settings_swift_key"
                       value="{{data['swift_key']}}">
            </div>
            <label class="control-label" for="settings_swift_key">
                Swift Auth URL
            </label>
            <div class="controls">
                <input type="text" class="input-medium" id="settings_swift_auth_url"
                       name="settings_swift_auth_url"
                       value="{{data['swift_auth_url']}}">
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
            <label class="control-label" for="settings_container">
                App Folder
            </label>
            <div class="controls">
                <input type="text" class="input-medium" id="settings_container"
                       name="settings_container"
                       value="{{data['container']}}">
                <p>Swift container under which all directories will be stored</p>
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
