<form name="watchdirs" action="/watchdirs" method="POST">
    <legend>Watched Directories</legend>
    <table class="table table-striped table-bordered">
        <thead>
            <tr>
                <th></th>
                <th>Path</th>
                <th>Added</th>
                <th>Last Change</th>
            </tr>
        </thead>
        <tbody>
            %for dirinfo in data['dirs']:
                <tr>
                    <td><input type="checkbox" name="watcheddirs"
                               value="{{dirinfo['directory']}}"></td>
                    <td>{{dirinfo['directory']}}</td>
                    <td>{{dirinfo['added']}}</td>
                    <td>{{dirinfo['changed']}}</td>
                </tr>
            %end
        </tbody>
    </table>
    <div class="form-actions">
        <button type="submit" class="btn btn-primary">Unwatch &raquo;</button>
    </div>
</form>
