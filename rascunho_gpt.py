Eu tenho um dataset composto por um banco de dados em sqlite. Ele possui 4 tabelas, bitrate_test, bitrate_train, rtt_test e rtt_train. Ignore por enquanto as tabelas _test e foque apenas nas _train. Segue abaixo o header delas. 

client,server,timestamp,bitrate
ba,ce,1717718915,3000
ba,ce,1717718916,66910
ba,ce,1717718916,294878
ba,ce,1717718916,351151
ba,ce,1717718916,329464
ba,ce,1717718916,388265

client,server,timestamp,rtt
ba,ce,1717718941,12.52
ba,ce,1717719217,12.59
ba,ce,1717719722,12.49
ba,ce,1717719841,12.49
ba,ce,1717720185,12.48


Modifique o código abaixo para criar um programa utilizando lang chain que receba do usuário uma pergunta em linguagem natural, gere a query sql necessária para pesquise na tabela correta e responda o usuário em linguagem natural. Utilize o conceito de Chain of Thoughts.



