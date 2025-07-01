<?php
 try {

    $arg1 = str_replace('{','',str_replace('}','',$argv[1]));
    $argumen = json_decode('[{'.$arg1.'}]', true);
    $nombre = $argumen[0]['nombre'];
    $apellido = $argumen[0]['apellido'];
    $password = $argumen[0]['password'];
    $usertipo = $argumen[0]['usertipo'];
    $nuevouser = $argumen[0]['newuser'];

    error_reporting(E_ALL);

    ini_set('display_errors', '1');

    @ldap_set_option(NULL, LDAP_OPT_DEBUG_LEVEL, 7);

    //$ldapConn = @ldap_connect('ldap://10.10.10.4:389') or die ("No se encuentra el servidor AD"); /// de esta forma si se conecta pero no se guarda
    $ldapConn = @ldap_connect('ldaps://10.10.10.4:636') or die ("No se encuentra el servidor AD"); //// de esta forma no se conecta


    @ldap_bind($ldapConn,"ITB\Administrador","S3rv3r1tb2019$") or die("No se puede acceder al AD!");


    $newUser = $nuevouser;

    $newUserNom = htmlspecialchars($nombre);

    $newUserApe = htmlspecialchars($apellido);

    $newUserTipo = htmlspecialchars($usertipo);


    $domincorreo = "@itb.edu.ec"
    if ($usertipo == 'ADMINISTRATIVO'){
        $domincorreo = "@bolivariano.edu.ec"
    }
    $newUserMail = $newUser.$domincorreo;

    $newUserPrinName = $newUser.$domincorreo;

    $newUserNomCom = $newUserNom.' '.$newUserApe;



    $pwdtxt = htmlspecialchars($password);
    $newPassword = '"' . $pwdtxt . '"';
    $newPass = iconv( 'UTF-8', 'UTF-16LE', $newPassword );

    //echo $newUserNomCom.' '.$newUserNom.' '.$newUserApe.' '.$newUser.' '.$newUserPrinName.' '.$newUserTipo.' '.$newPass.' '.$newUserMail.' '.$pwdtxt ;

    $dn_user = "CN=$newUserNomCom,CN=Users,DC=itb,DC=edu,DC=ec";

    //$ldaprecord['cn'] = "TEST_NOM";

    $ldaprecord['givenName'] = $newUserNom; //nombres

    $ldaprecord['sn'] = $newUserApe; // apellidos

    $ldaprecord['sAMAccountName'] = $newUser; //nombre de usuario

    $ldaprecord['UserPrincipalName'] = $newUserPrinName; // correo completo .local

    $ldaprecord['displayName'] = $newUserNomCom; //nombre

    $ldaprecord['description'] = $newUserTipo;

    $ldaprecord["unicodePwd"] = $newPass;

    $ldaprecord['name'] = $newUserNomCom; //nombre completo

    $ldaprecord['UserAccountControl'] = "65536"; //permisos

    $ldaprecord['objectclass'][0] = 'top';

    $ldaprecord['objectclass'][1] = 'person';

    $ldaprecord['objectclass'][2] = 'organizationalPerson';

    $ldaprecord['objectclass'][3] = 'user';

    $ldaprecord['mail'] = $newUserMail; // correo completo .itb.edu.ec

    if(@ldap_add($ldapConn, $dn_user, $ldaprecord))
    {
        echo "Usuario creado: $newUserNomCom";
    }
    else
    {
       echo "LDAP-Errno: " . ldap_errno($ldapConn) . "<br />";
       echo "LDAP-Error: " . ldap_error($ldapConn) . "<br />";
    }
    @ldap_unbind($ldapConn);

 } catch (Exception $e) {
    echo 'Excepción capturada: ',  $e->getMessage(), "\n";
 }

?>