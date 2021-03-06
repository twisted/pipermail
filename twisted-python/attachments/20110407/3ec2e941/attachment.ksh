@prefix : <http://example.com/twisted#> .

[ a :Server;

    :binder     [   :port 80;
                    :ip   "0.0.0.0" ];

    :binder     [   :port 443;
                    :ip "0.0.0.0";
                    :pem "server.pem" ];

	:app        [   :description "Some app";
                    :resource "someapp.SomeApp";
                    :path "/someapp";
                    :users "authdomains/someapp" ];
 
	:app        [   :description """My tiny little app...

...with verbose multi-line description text!
	""";
                    :resource "myapp.MyRootApp";
                    :path "/";
                    :users "authdomains/myapp" ];


].

[ a :Server;

    :binder     [   :port 2020;
                    :ip   "127.0.0.1" ];

    :app        [   :resource "anotherapp.AnotherApp";
                    :path "/";
                ];
].

