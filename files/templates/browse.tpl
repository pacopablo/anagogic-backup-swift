<!DOCTYPE html>
<!--[if lt IE 7]>      <html class="no-js lt-ie9 lt-ie8 lt-ie7"> <![endif]-->
<!--[if IE 7]>         <html class="no-js lt-ie9 lt-ie8"> <![endif]-->
<!--[if IE 8]>         <html class="no-js lt-ie9"> <![endif]-->
<!--[if gt IE 8]><!--> <html class="no-js"> <!--<![endif]-->
<head>
    <meta charset="utf-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge,chrome=1">
    <title></title>
    <meta name="description" content="">
    <meta name="viewport" content="width=device-width">

    <link rel="stylesheet" href="/css/bootstrap.min.css">
    <style>
        body {
            padding-top: 60px;
            padding-bottom: 40px;
        }
    </style>
    <link rel="stylesheet" href="/css/bootstrap-responsive.min.css">
    <link rel="stylesheet" href="/css/main.css">

    <script src="/js/vendor/modernizr-2.6.1-respond-1.1.0.min.js"></script>
</head>
<body>
<!--[if lt IE 7]>
<p class="chromeframe">You are using an outdated browser. <a href="http://browsehappy.com/">Upgrade your browser today</a> or <a href="http://www.google.com/chromeframe/?redirect=true">install Google Chrome Frame</a> to better experience this site.</p>
<![endif]-->

<!-- This code is taken from http://twitter.github.com/bootstrap/examples/hero.html -->

<div class="navbar navbar-inverse navbar-fixed-top">
    <div class="navbar-inner">
        <div class="container">
            <a class="btn btn-navbar" data-toggle="collapse" data-target=".nav-collapse">
                <span class="icon-bar"></span>
                <span class="icon-bar"></span>
                <span class="icon-bar"></span>
            </a>
            <a class="brand" href="#">Anagogic Backup</a>
            <div class="nav-collapse collapse">
                <ul class="nav">
                    <li><a href="/index.html">Home</a></li>
                    <li class="active"><a href="/browse.html">Browse</a></li>
                    <li><a href="#contact">Contact</a></li>
                    <li class="dropdown">
                        <a href="#" class="dropdown-toggle" data-toggle="dropdown">Dropdown <b class="caret"></b></a>
                        <ul class="dropdown-menu">
                            <li><a href="#">Action</a></li>
                            <li><a href="#">Another action</a></li>
                            <li><a href="#">Something else here</a></li>
                            <li class="divider"></li>
                            <li class="nav-header">Nav header</li>
                            <li><a href="#">Separated link</a></li>
                            <li><a href="#">One more separated link</a></li>
                        </ul>
                    </li>
                </ul>
                <form class="navbar-form pull-right">
                    <input class="span2" type="text" placeholder="Email">
                    <input class="span2" type="password" placeholder="Password">
                    <button type="submit" class="btn">Sign in</button>
                </form>
            </div><!--/.nav-collapse -->
        </div>
    </div>
</div>

<div class="container-fluid">
    %if restartneeded:
    <div class="row-fluid">
        <div class="alert">
            <button type="button" class="close" data-dismiss="alert">X</button>
            The server needs to be restarted to change the hostname and port used
        </div>
    </div>
    %end
    %if internalerror:
    <div class="row-fluid">
        <div class="alert">
            <button type="button" class="close" data-dismiss="alert">X</button>
            The Anagogic Backup service encountered an internal error.
            Check the event log for details.
        </div>
    </div>
    %end
    <div class="row-fluid">
        <div class="span12">
            <legend>Watched Directories</legend>
            <table class="table table-striped table-bordered">
                <thead>
                <tr>
                    <th>Path</th>
                    <th>Size</th>
                    <th>Last Change</th>
                </tr>
                </thead>
                <tbody>
                %for dirinfo in dirs:
                <tr>
                    <td><a href="/view?path={{dirinfo['path_encoded']}}">{{dirinfo['path']}}</a></td>
                    <td>{{dirinfo['size']}}</td>
                    <td>{{dirinfo['changed']}}</td>
                </tr>
                %end
                </tbody>
            </table>
        </div>
    </div>

    <hr>

    <footer>
        <p>&copy; Anagogic 2012</p>
    </footer>

</div> <!-- /container -->

<script src="//ajax.googleapis.com/ajax/libs/jquery/1.8.0/jquery.min.js"></script>
<script>window.jQuery || document.write('<script src="/js/vendor/jquery-1.8.0.min.js"><\/script>')</script>

<script src="/js/vendor/bootstrap.min.js"></script>

<script src="/js/main.js"></script>

</body>
</html>