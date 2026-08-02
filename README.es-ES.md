

# Orden automática de OVH ECO

## Propósito de este programa

OVHcloud modificó la línea ECO en septiembre de 2024. La nueva línea ofrece una relación calidad-precio increíble, por lo que es evidente que el stock es limitado y se agota muy rápido.

En este programa puedes realizar pedidos a través de la API de OVHcloud y ejecutarlo como un script o en un contenedor para realizar el pedido cuando esté disponible!

> No eres el único que usa esto, por lo que tu éxito no está garantizado

> La API puede cambiar, eliminarse o el software puede cometer cualquier error que afecte tu pedido, por lo que úsalo bajo tu propio riesgo!

> Dado que este script consulta la API de disponibilidad de servidores de OVHcloud y, si es necesario, la API del catálogo, requiere una mayor cantidad de datos.

## Configuración

Probado en la subsidiaria IE, probablemente funcione en otras, pero no se ha probado.
Proyecto basado en [OVHcloud Python wrapper](https://github.com/ovh/python-ovh), consulta con este respecto a la configuración de subsidiarias y más.

### Configurar la API

Crea una clave de API [aquí](https://api.ovh.com/createToken/index.cgi?GET=/*&PUT=/*&POST=/*&DELETE=/*) y anota su información.
> Nota: Selecciona la caducidad adecuada. La mejor opción es 30 días; evita usar acceso ilimitado, es más seguro si la recreas cada 30 días.
Crea un archivo `.env` para permitir que dotenv lo lea y coloca la configuración aquí dentro.
```
OVH_ENDPOINT='ovh-eu'
OVH_APPLICATION_KEY='XXX'
OVH_APPLICATION_SECRET='XXX'
OVH_CONSUMER_KEY='XXX'
```
> Los endpoints disponibles en el enlace superior, usa el que coincida con tu cuenta.
> Sugiero usar VsCode para crear los archivos y gestionarlos.

### Configurar tus pedidos deseados

necesitas crear el archivo `preferences.json`.
Aquí hay un ejemplo del contenido JSON para ello.

#### JSON RAW
```
{
  "subsidiary": "IE",
  "user_servers": [
    {
      "planCode": "25skleb01",
      "fqn": "25skleb01.ram-32g-ecc-2400.softraid-2x450nvme",
      "skip_validate": false,
      "place_order": false,
      "autopay": false,
      "coupons": ["MONDAY"],
      "datacenters": [
        {
          "region": "europe",
          "dedicated_datacenter": "fra"
        },
        {
          "region": "europe",
          "dedicated_datacenter": "gra"
        }
      ],
      "labels": {
        "dedicated_os": "none_64.en"
      },
      "addon_planCodes": [
        "softraid-2x450nvme-25skle",
        "bandwidth-300-25skle",
        "ram-32g-ecc-2400-25skle"
      ],
      "qty": 1,
      "ceiling_price": 20.0,
      "dc_carts": {}
    }
  ]
}
```

#### Explicación

El JSON contiene la subsidiaria para la colocación del pedido (IE) y los servidores del usuario.

User servers es un array que contiene los servicios. Debes rellenar un elemento del array siguiendo este ejemplo, pero es importante que el script lo edite, almacene la información del carrito específica del producto y otras cosas. Por lo tanto, siempre escribe este elemento mínimo del array (amplíalo si necesitas más de 2 servidores) pero mantén esta estructura y deja que el script lo utilice.

Un servidor contiene información importante:
- La FQN, planCode, labels, addon planCodes, datacenters.
> Esta información está especificada en [OVH API](https://eu.api.ovh.com/console/). Consulta las secciones de pedido y servidor dedicado.
- QTY y ceiling price son dos variables importantes. Establece la cantidad deseada en un carrito y establece el precio máximo de la primera factura (excl. IVA). Si el precio es mayor a esto, el cliente no realiza el pedido y establece qty, price a 0 para eliminarlo de comprobaciones futuras. La primera factura puede incluir los costos de configuración, por lo que, por ejemplo, si quieres pedir KS-LE-B con 9.9 mensuales y 9.9 euros de costo de configuración, necesitas establecer un ceiling price de 20 eur.
- De los labels solo se necesita uno. Establece dedicated_os.
- La dedicated_datacenter también es un label. Sin embargo, si la estableces en esta estructura JSON como en el ejemplo, el programa intenta realizar el pedido simultáneamente en FRA y GRA. Si está disponible en FRA o GRA, realiza el pedido y establece qty a 0 (por lo tanto, detiene el pedido). Esto ayuda a pedir un servidor con múltiples preferencias de DC, si la disponibilidad es más importante que la ubicación explícita para un bare metal poco común.
> Si quieres realizar un pedido tanto en gra como en fra, simplemente crea otro elemento y modifica el primero para que sea solo fra y el segundo solo gra. por lo que el array datacenter debe contener solo un elemento en ambos servidores.
- Para los addons debes colocar todos los planCodes de addons obligatorios. Si no lo haces y falta solo uno, el pedido fallará.
- skip_validate: Establécelo en true si quieres omitir la validación del pedido
> Si se omite la validación del pedido, se omite el ceiling price y el producto se pide a cualquier precio. Esto hace que la velocidad sea más rápida.
- place_order: Establécelo explícitamente en true. Si no lo haces, solo se creará un plan de pedido.
> Ten en cuenta que si esto se establece en false, la cantidad se establece en 0 después de la validación. Por lo tanto, si creas un pedido y solo lo validas, para ordenarlo, cierra la APP, establece la cantidad y reiníciala. Este comportamiento corrige el problema de que múltiples revisiones aumentan la carga de red y el tiempo consumido por el script.
- autopay: Controla que después del pedido, el pago se procese automáticamente o no
> Si estableces esto en false, hasta que no pagues el pedido no se realizará, por lo que puedes perder tu oportunidad de obtener el servidor.
- coupons: Un array que contiene los códigos de cupón para el pedido
- dc_carts: Vacío, almacena la información del carrito específica del datacenter. Por defecto no necesita modificación manual.

Por lo tanto, cuando inicies el script por primera vez después de una configuración personalizada, rellenará la(s) información(es) del carrito según tus necesidades.
Cuando expire (después de un mes) el script crea uno nuevo.
Solo se verifican y planifican los servidores que tienen qty mayor que cero.

Subsidiary: Depende de tu endpoint de API. Se usa al crear pedidos. Puedes obtener la lista de subsidiarias y seleccionar la tuya, dependiendo de tu cuenta.
- [CA](https://ca.api.ovh.com/console/?section=%2Fdedicated%2Fserver&branch=v1#get-/dedicated/server/availabilities)
- [EU](https://eu.api.ovh.com/console/?section=%2Fdedicated%2Fserver&branch=v1#get-/dedicated/server/availabilities)
- [US](https://api.us.ovhcloud.com/console/?section=%2Forder&branch=v1#get-/order/catalog/public/eco)
> usa siempre letras mayúsculas.

### Autocompletado desde el catálogo

> Esta función es muy, muy experimental. ¡Úsala bajo tu propio riesgo!!!

> Esta función consulta el catálogo de la API de EU. En el futuro será compatible con CA y US.

> Esta función consume una gran cantidad de datos. ¡Úsala bajo tu propio riesgo!

Puedes instruir a la API para que consulte el catálogo de servidores y obtenga los datos de él cuando estén disponibles.
Esta función te ayuda si quieres conseguir un servidor que aparece en la API de disponibilidad pero aún no está disponible en el catálogo. Por ejemplo, KS-LE-2 apareció en octubre como 25skle02 con bajo stock en rbx. Si lo configuras, puedes ordenarlo después de que OVH lo rellene en el carrito.
Si configuras el fetcher, obtiene los datos del catálogo y, si lo configuras, lo ordena según tus necesidades.

Aquí está el JSON raw para esto. Puedes combinar múltiples servidores con múltiples opciones en el array. Por lo tanto, por ejemplo, simplemente puedes insertar KS-LE-B y 25skle02.
> Advertencia: Mientras uno o más servidores requieran el catálogo, se descarga periódicamente lo que aumenta drásticamente el tráfico de red. ¡Úsalo bajo tu propio riesgo!

```
{
  "subsidiary": "IE",
  "user_servers": [
    {
      "planCode": "24sk50",
      "fqn": "24sk50.ram-32g-ecc-2400.softraid-2x2000sa",
      "skip_validate": false,
      "place_order": false,
      "autopay": false,
      "coupons": ["MONDAY"],
      "fetch_catalog": {
        "storage": "",
        "memory": "",
        "bandwidth": ""
      },
      "datacenters": [
        {
          "region": "europe",
          "dedicated_datacenter": "gra"
        },
        {
          "region": "europe",
          "dedicated_datacenter": "fra"
        }
      ],
      "labels": {
        "dedicated_os": "none_64.en"
      },
      "addon_planCodes": [],
      "qty": 1,
      "ceiling_price": 50.0,
      "dc_carts": {}
    }
  ]
}
```

Explicación:
- El addon_planCodes está vacío, se rellenará cuando la configuración esté disponible en el catálogo.
- Establece en `fetch_catalog` las partes que quieres obtener. En Kimsufi, estos son bandwidth, memory y storage. Estas son cadenas vacías, pero si prefieres, puedes precargarlas y en este caso solo se copian a addons. Si omites cualquier campo obligatorio, el servidor probablemente no se ordenará.
- Después de rellenar los datos desde el catálogo, el proceso es normal. Según tus necesidades, crea los datos raw y los agrega al archivo json.
> En situaciones raras es posible que FQN y el catálogo no sean consistentes, especialmente en 500/512 GB NVMe y algunos modelos especiales de servidor RAM. Si solo es posible una opción de RAM y almacenamiento, no es un problema ya que el script usa la predeterminada.

## Ejecutarlo

ejecútalo como un script de Python simple
```
pip install -r requirements.txt
python3 order.py
```

O en Docker (ver paquetes).

Si lo ejecutas en Docker, vincula el `preferences.json` al directorio `/app` y vincula el `.env` al directorio `/app`. Opcionalmente, vincula `offers.json` si quieres acceder al catálogo desde el sistema host.

## Ejecutarlo en Docker

Clona este repositorio y ejecuta 
`docker compose build`
`docker compose up -d`.

# Observaciones

Este script utiliza la API de OVHcloud. ECO y otros nombres son propiedad de OVHcloud.
