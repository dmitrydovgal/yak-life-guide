"""Регіональні комунальні сервіси — чернетка бази для MVP «Місцеві сервіси».

Один запис = один сервіс (сайт/кабінет). Він може обслуговувати кілька громад і постачальників.
Публікуємо лише status='verified'. 'partial' — офіційний сайт є, але частину можливостей
не підтверджено публічним джерелом. 'unconfirmed' — не показуємо.

Можливості (ACTIONS): True — підтверджено джерелом, False — підтверджено, що немає,
None — не вдалося підтвердити (на сайті Як? не показуємо як можливість).

Перевірка 27.11.2026: лише публічні сторінки, без входу в кабінети й без персональних даних.
"""

CHECKED = '2026-11-27'

TYPES = {
    'unified': 'Єдиний рахунок / розрахунковий центр',   # кілька постачальників в одному кабінеті
    'utility': 'Кабінет постачальника',                  # водоканал, тепло
    'network': 'Оператор мережі',                        # газорозподіл, електромережі
    'supplier': 'Постачальник енергії',                  # газ, електроенергія (може бути обраний споживачем)
    'payment': 'Платіжний сервіс',                       # приймає оплату, але не веде нарахувань
}
UTIL = {'water': 'Вода й водовідведення', 'heat': 'Опалення й гаряча вода', 'gas': 'Газ',
        'gasdist': 'Розподіл газу', 'power': 'Електроенергія', 'waste': 'Вивезення відходів',
        'house': 'Утримання будинку', 'other': 'Інші послуги',
        'multi': 'Кілька послуг (перелік — у кабінеті сервісу)'}
ACTIONS = {'pay': 'Оплатити', 'readings': 'Передати показники', 'debt': 'Перевірити борг і нарахування',
           'bill': 'Отримати рахунок', 'history': 'Історія платежів'}

# Громади/міста. id — латиницею, щоб потім стати частиною URL, якщо погодимо сторінки міст.
PLACES = {
    'kyiv': {'name': 'Київ', 'oblast': 'м. Київ'},
    'dnipro': {'name': 'Дніпро', 'oblast': 'Дніпропетровська'},
    'kryvyi-rih': {'name': 'Кривий Ріг', 'oblast': 'Дніпропетровська'},
    'kharkiv': {'name': 'Харків', 'oblast': 'Харківська'},
    'odesa': {'name': 'Одеса', 'oblast': 'Одеська'},
    'lviv': {'name': 'Львів', 'oblast': 'Львівська'},
    'zaporizhzhia': {'name': 'Запоріжжя', 'oblast': 'Запорізька'},
    'mykolaiv': {'name': 'Миколаїв', 'oblast': 'Миколаївська'},
    'vinnytsia': {'name': 'Вінниця', 'oblast': 'Вінницька'},
    'poltava': {'name': 'Полтава', 'oblast': 'Полтавська'},
    'kremenchuk': {'name': 'Кременчук', 'oblast': 'Полтавська'},
    'horishni-plavni': {'name': 'Горішні Плавні', 'oblast': 'Полтавська'},
    'chernihiv': {'name': 'Чернігів', 'oblast': 'Чернігівська'},
    'cherkasy': {'name': 'Черкаси', 'oblast': 'Черкаська'},
    'sumy': {'name': 'Суми', 'oblast': 'Сумська'},
    'zhytomyr': {'name': 'Житомир', 'oblast': 'Житомирська'},
    'khmelnytskyi': {'name': 'Хмельницький', 'oblast': 'Хмельницька'},
    'chernivtsi': {'name': 'Чернівці', 'oblast': 'Чернівецька'},
    'rivne': {'name': 'Рівне', 'oblast': 'Рівненська'},
    'ivano-frankivsk': {'name': 'Івано-Франківськ', 'oblast': 'Івано-Франківська'},
    'ternopil': {'name': 'Тернопіль', 'oblast': 'Тернопільська'},
    'lutsk': {'name': 'Луцьк', 'oblast': 'Волинська'},
    'uzhhorod': {'name': 'Ужгород', 'oblast': 'Закарпатська'},
    'kropyvnytskyi': {'name': 'Кропивницький', 'oblast': 'Кіровоградська'},
    'kherson': {'name': 'Херсон', 'oblast': 'Херсонська'},
}


def S(id, name, type, url, places, util, actions, status, sources, *, operator='', cabinet='',
      providers=None, limits='', howto=None, scope=None, app=None):
    """scope: {place_id: 'частина міста …'}, якщо сервіс діє не на всій території."""
    return dict(id=id, name=name, type=type, url=url, cabinet=cabinet or url, operator=operator, places=places,
                scope=scope or {}, util=util, providers=providers or [], actions=actions, limits=limits,
                howto=howto or [], app=app, sources=sources, checked=CHECKED, status=status)


def A(pay=None, readings=None, debt=None, bill=None, history=None, reg=None):
    return {'pay': pay, 'readings': readings, 'debt': debt, 'bill': bill, 'history': history, 'register': reg}


SERVICES = [
    # ── Єдині рахунки / розрахункові центри ───────────────────────────────────────────
    S('novakom', 'НОВА-КОМ (ЄМАСКР)', 'unified', 'https://www.novakom.com.ua/', ['kryvyi-rih'],
      ['water', 'heat', 'gas', 'power', 'house', 'waste', 'other'],
      A(pay=True, readings=True, debt=True, bill=True, history=True, reg=True), 'verified',
      [('https://www.novakom.com.ua/about/faq.html', 'FAQ: оплата в кабінеті або застосунку, показники, єдиний рахунок'),
       ('https://www.novakom.com.ua/', 'Меню кабінету: суми до сплати, показники, історія платежів, розшифровка нарахувань')],
      operator='ТОВ «НОВА-КОМ»', app='НОВА-КОМ (Google Play, App Store)',
      providers=['Постачальники, підключені до ЄМАСКР (перелік — на сайті, розділ «Телефони підприємств»)'],
      limits='Показує лише постачальників, підключених до системи. Нарахування робить сам постачальник — питання щодо суми до нього.',
      howto=['Зареєструйтеся в Кабінеті споживача на novakom.com.ua або в застосунку.',
             'Додайте адресу й введіть комунальний код (його можна отримати на сайті).',
             'Відкрийте «Сплатити», за потреби внесіть показники лічильників і підтвердьте оплату.']),
    S('infocentr-hp', 'Інформаційний центр (ЄМАСКР)', 'unified', 'https://hp.infocentr.pl.ua/', ['horishni-plavni'],
      ['heat', 'water', 'other'], A(debt=True, reg=None), 'partial',
      [('https://hp.infocentr.pl.ua/about/faq.html', 'FAQ: кабінет абонента за адресою й комунальним кодом'),
       ('https://hp.infocentr.pl.ua/about/public/offer.html', 'Публічна оферта ЄМАСКР')],
      limits='Оплату й передачу показників на публічних сторінках не підтверджено.'),
    S('ckc-kyiv', 'Центр комунального сервісу (ЦКС)', 'unified', 'https://cks.com.ua/', ['kyiv'],
      ['water', 'heat', 'house', 'other'], A(pay=True, readings=True, debt=True, bill=True, history=True, reg=True), 'verified',
      [('https://kyivcity.gov.ua/news/tsentr_komunalnogo_servisu_nagaduye_kiyanam_pro_perevagi_vikoristannya_osobistogo_kabinetu_spozhivacha_ta_prostiy_algoritm_reyestratsi_v_nomu/',
        'Портал Києва (26.04.2024): кабінет — кілька адрес, оплата всіх послуг разом або окремо, показники, історія, копія рахунку'),
       ('https://cks.com.ua/to_consumers/our-services/', 'Сайт ЦКС: єдина абонентська служба')],
      operator='Комунальний концерн «Центр комунального сервісу»', cabinet='https://komunalka.ua/',
      limits='Лише послуги, нарахування яких веде ЦКС. Газ і електроенергію оплачують своїм постачальникам.',
      howto=['На сайті ЦКС натисніть «Особистий кабінет» → «Зареєструватися» (ПІБ, пошта, телефон).',
             'Додайте квартиру за даними з рахунку.', 'Оплачуйте все разом або окремо, передавайте показання квартирних лічильників.']),
    S('gioc-kyiv', 'ГІОЦ', 'unified', 'https://www.gioc.kiev.ua/', ['kyiv'], ['other'], A(reg=True), 'partial',
      [('https://kyivcity.gov.ua/news/kiyanam_nagaduyut_pro_mozhlivist_oplati_komunalnikh_poslug_onlayn/', 'Портал Києва згадує кабінет ГІОЦ як спосіб оплати')],
      operator='КП «ГІОЦ»'),
    S('pay-vn', '«Єдиний Рахунок» (pay.vn.ua)', 'unified', 'https://pay.vn.ua/', ['vinnytsia'],
      ['water', 'heat', 'house', 'waste', 'other'], A(pay=True, readings=True, debt=True, reg=True), 'verified',
      [('https://pay.vn.ua/', 'FAQ: кабінет, додати помешкання за особовим рахунком, оплата, стан рахунку; Вінницький район'),
       ('https://allbill.com.ua/', 'Проєкт «Єдиний Рахунок»: подання показників і оплата')],
      operator='Центр муніципальних систем управління (ЦМСМ)', app='Єдиний Рахунок',
      scope={'vinnytsia': 'Вінниця та населені пункти Вінницького району (вибір у полі адреси)'},
      howto=['Зареєструйтеся на pay.vn.ua або в застосунку «Єдиний Рахунок».',
             'Натисніть «Додати помешкання»: адреса, особовий рахунок із рахунку й прізвище.',
             'Перевірте нарахування, внесіть показники й оплатіть.']),
    S('mirc-mykolaiv', 'МІРЦ — єдиний рахунок', 'unified', 'https://www.girc.online/', ['mykolaiv'],
      ['house', 'water', 'heat', 'other'], A(pay=True, debt=True, bill=True, readings=None, reg=False), 'verified',
      [('https://www.girc.online/', 'Єдиний рахунок-повідомлення для Миколаєва; оплата через ПриватБанк; дані оновлюються 7-го числа'),
       ('https://my.girc.online/', 'Кабінет: рахунок за адресою або за номером ЄОР')],
      operator='ТОВ «Міський інформаційно-розрахунковий центр»', cabinet='https://my.girc.online/',
      limits='Передавання показників не підтверджено. Оплата — через банк за посиланням із сайту.',
      howto=['Відкрийте my.girc.online.', 'Знайдіть рахунок за адресою або номером єдиного особового рахунку (ЄОР).',
             'Оплатіть за посиланням «Швидко оплатити у ПриватБанку».']),
    S('erc-chernivtsi', 'Єдиний розрахунковий центр', 'unified', 'https://erc.chv.ua/', ['chernivtsi'],
      ['water', 'heat', 'waste', 'other'], A(debt=True, reg=False), 'partial',
      [('https://erc.chv.ua/index.php/ua/', 'Розділ «Дізнатись заборгованість»; перелік кабінетів постачальників; прийом мешканців припинено')],
      limits='Особистий прийом у ЄРЦ припинено. Оплата — через постачальників або банк.'),
    S('mycity-khm', 'My City — єдина квитанція', 'unified', 'https://mycity.khm.gov.ua/', ['khmelnytskyi'],
      ['water', 'heat', 'house', 'other'], A(reg=True), 'partial',
      [('https://mycity.khm.gov.ua/', 'Єдина інформаційна система міста: сервіс «Єдина квитанція», кабінет мешканця')],
      operator='КП «Хмельницькінфоцентр» (Хмельницька міська рада)',
      limits='Конкретні можливості кабінету на публічних сторінках не описано.'),
    S('ekc-kremenchuk', 'Єдина Комунальна Система (ЄКС)', 'unified', 'https://ekc.com.ua/', ['kremenchuk'],
      ['heat', 'water', 'power', 'other'], A(pay=True, readings=None, reg=False), 'partial',
      [('https://ekc.com.ua/ua/', 'Персональний кабінет, «Сплатити онлайн без реєстрації», новини Кременчуцької ТЕЦ')],
      limits='Сервіс не публікує окремого переліку міст і постачальників; що він працює в Кременчуці, видно з його новин.'),
    S('erckp-dnipro', 'ЄРЦ КП — портал споживачів', 'unified', 'https://complatezh.info/', ['dnipro'],
      ['house', 'waste', 'gas', 'other'], A(pay=True, readings=True, bill=True, reg=True), 'partial',
      [('https://complatezh.info/', 'Кабінет, оплата, «Передати показання», рахунок-повідомлення, застосунок, Viber-бот')],
      operator='ТОВ «ЄРЦ КП»', app='ЄРЦ КП',
      limits='Рішення міської ради, яке робить ЄРЦ КП офіційною системою Дніпра, ми не знайшли.'),
    S('infolviv', 'Портал споживачів комунальних послуг', 'unified', 'https://infolviv.com.ua/', ['lviv'],
      ['water'], A(readings=True, reg=True), 'partial',
      [('https://lvivvodokanal.com.ua/residents/podaty-pokaznyky/', 'Львівводоканал посилається на «Портал споживачів» для показників')],
      limits='Підтверджено лише для води (Львівводоканал). Інші послуги — не підтверджено.'),

    # ── Платіжні сервіси (не плутати з офіційними системами міста) ───────────────────────
    S('gerc-odesa', 'ГЕРЦ', 'payment', 'https://www.gerc.ua/ua/', ['odesa'], ['other'], A(pay=True, debt=True, reg=None), 'partial',
      [('https://www.gerc.ua/ua/', 'Оплата комунальних та інших платежів, інформація про заборгованість'),
       ('https://www.gerc.ua/ua/contacts/', 'Одеса, вул. Єврейська, 2а')],
      limits='Фінансова компанія, що приймає платежі. Рішення міської ради, яке робить її офіційною системою Одеси, ми не знайшли.'),

    # ── Водоканали ───────────────────────────────────────────────────────────────────────
    S('kharkivvodokanal', 'Харківводоканал — особистий кабінет', 'utility', 'https://vodokanal.kharkov.ua/', ['kharkiv'], ['water'],
      A(readings=True, bill=True, history=True, reg=True), 'partial',
      [('https://vodokanal.kharkov.ua/news/3794', 'Новина водоканалу (2017): у кабінеті передають показання, формують квитанції, дивляться статистику оплат')],
      cabinet='https://billing.vodokanal.kharkov.ua/', limits='Джерело 2017 року — можливості могли змінитися.'),
    S('infoxvodokanal', 'Інфоксводоканал — особистий кабінет', 'utility', 'https://infoxvod.com.ua/', ['odesa'], ['water'],
      A(readings=None, reg=True), 'partial',
      [('https://cpp.infoxvod.com.ua/', 'Сторінка входу в особистий кабінет абонента для населення'),
       ('https://infoxvod.com.ua/uk/poriadok-i-sposobi-oplati/', 'Порядок і способи оплати')],
      operator='ТОВ «Інфокс», філія «Інфоксводоканал»', cabinet='https://cpp.infoxvod.com.ua/'),
    S('zp-vodokanal', 'Водоканал Запоріжжя — особистий кабінет', 'utility', 'https://vodokanal.zp.ua/', ['zaporizhzhia'], ['water'],
      A(reg=True), 'partial', [('https://cpp.vodokanal.zp.ua/', 'Особистий кабінет абонента для населення')],
      operator='КП «Водоканал» Запорізької міської ради', cabinet='https://cpp.vodokanal.zp.ua/'),
    S('dnipro-vodokanal', 'Дніпроводоканал', 'utility', 'https://vodokanal.dp.ua/', ['dnipro'], ['water'], A(), 'unconfirmed',
      [('https://cent.vodokanal.dp.ua/', 'Кабінет для підприємств та організацій (не для населення)')],
      limits='Кабінет для населення не знайдено.'),
    S('lviv-vodokanal', 'Львівводоканал', 'utility', 'https://lvivvodokanal.com.ua/', ['lviv'], ['water'],
      A(readings=True, reg=None), 'verified',
      [('https://lvivvodokanal.com.ua/residents/podaty-pokaznyky/', 'Подати показники: портал споживачів, SMS за районами')],
      operator='ЛМКП «Львівводоканал»', cabinet='https://infolviv.com.ua/',
      howto=['Відкрийте «Подати показники» на сайті Львівводоканалу.', 'Оберіть портал споживачів або SMS на номер свого району.']),
    S('dnipro-kirovograd', 'ОКВП «Дніпро-Кіровоград»', 'utility', 'https://my.dnipro-kirovograd.com.ua/', ['kropyvnytskyi'], ['water'],
      A(readings=True, reg=True), 'verified',
      [('https://my.dnipro-kirovograd.com.ua/', 'Особистий кабінет споживача (населення); Telegram-бот для показників')],
      cabinet='https://my.dnipro-kirovograd.com.ua/', limits='Обласне підприємство: перевірте, що саме воно вказане у вашому рахунку.'),
    S('poltava-vodokanal', 'Полтававодоканал — особистий кабінет', 'utility', 'https://vodokanal.poltava.ua/', ['poltava'], ['water'],
      A(pay=True, bill=True, debt=True, reg=True), 'verified',
      [('https://vodokanal.poltava.ua/uk/', 'Кабінет для населення: контроль рахунків, оплата, квитанції')],
      operator='КП ПОР «Полтававодоканал»'),
    S('cherkasy-vodokanal', 'Черкасиводоканал — особистий кабінет', 'utility', 'https://vodokanal-cherkasy.ck.ua/', ['cherkasy'], ['water'],
      A(pay=True, readings=True, debt=True, reg=True), 'verified',
      [('https://my.vodokanal-cherkasy.ck.ua/main/', 'Кабінет: показники за кількома рахунками, оплата, дані про розрахунки')],
      cabinet='https://my.vodokanal-cherkasy.ck.ua/main/'),
    S('chernivtsi-vodokanal', 'Чернівціводоканал', 'utility', 'https://vodokanal.cv.ua/', ['chernivtsi'], ['water'],
      A(bill=True, reg=True), 'partial', [('https://vodokanal.cv.ua/', 'Особистий кабінет (завантажити рахунок), чат-бот')]),
    S('khm-vodokanal', 'Хмельницькводоканал', 'utility', 'https://water.km.ua/', ['khmelnytskyi'], ['water'],
      A(pay=None, reg=True), 'partial', [('https://water.km.ua/', 'Особистий кабінет побутового споживача, оплата онлайн')]),
    S('kherson-vodokanal', 'Херсонський водоканал', 'utility', 'https://water.kherson.ua/', ['kherson'], ['water'],
      A(), 'partial', [('https://water.kherson.ua/', 'Офіційний сайт МКП «Херсонський водоканал»')]),
    S('sumy-vodokanal', 'Міськводоканал Суми', 'utility', 'https://vodokanal.sumy.ua/', ['sumy'], ['water'], A(), 'unconfirmed',
      [('https://vodokanal.sumy.ua/', 'Сайт обмежив автоматичні запити (429) — перевірити вручну')]),

    # ── Тепло ────────────────────────────────────────────────────────────────────────────
    S('hts-kharkiv', 'Харківські теплові мережі — особистий кабінет', 'utility', 'https://www.hts.kharkov.ua/', ['kharkiv'], ['heat'],
      A(readings=True, debt=True, reg=False), 'verified',
      [('https://www.hts.kharkov.ua/cabinet/login', 'Кабінет: показання лічильників гарячої води й тепла, стан рахунку; вхід за особовим рахунком і прізвищем')],
      cabinet='https://www.hts.kharkov.ua/cabinet/login',
      howto=['Відкрийте кабінет на сайті ХТМ.', 'Увійдіть за особовим рахунком і прізвищем або зареєструйтеся, щоб додати кілька квартир.',
             'Внесіть показання й перевірте стан рахунку.']),
    S('kte-kyiv', 'Київтеплоенерго — особистий кабінет', 'utility', 'https://kte.kmda.gov.ua/', ['kyiv'], ['heat'], A(reg=True), 'partial',
      [('https://kte.kmda.gov.ua/my-cabinet/user', 'Особистий кабінет з гарячої води та опалення')], cabinet='https://kte.kmda.gov.ua/my-cabinet/user'),
    S('teploenergo-dnipro', 'КП «Теплоенерго» (Дніпро)', 'utility', 'https://teploenergo.dp.ua/', ['dnipro'], ['heat'], A(debt=True), 'partial',
      [('https://teploenergo.dp.ua/', 'Розділ «Перевірити, чи є борг?»')]),
    S('teplo-odesa', 'Теплопостачання міста Одеси — особистий кабінет', 'utility', 'https://www.teplo.od.ua/', ['odesa'], ['heat'],
      A(reg=True), 'partial', [('https://cabinet.teplo.od.ua/', 'Особистий кабінет КП «Теплопостачання міста Одеси»')], cabinet='https://cabinet.teplo.od.ua/'),
    S('lte-lviv', 'Львівтеплоенерго', 'utility', 'https://lte.lviv.ua/', ['lviv'], ['heat'], A(reg=True), 'partial',
      [('https://lte.lviv.ua/', 'Посилання «Особистий кабінет»')]),
    S('poltava-teplo', 'Полтаватеплоенерго', 'utility', 'https://te.pl.ua/', ['poltava'], ['heat'], A(pay=True, readings=True), 'verified',
      [('https://te.pl.ua/', '«Сплатити», «Передати показання», чат-бот')]),
    S('otke-chernihiv', 'АТ «Облтеплокомуненерго»', 'utility', 'https://new.teplo.cn.ua/', ['chernihiv'], ['heat'], A(readings=True), 'verified',
      [('https://new.teplo.cn.ua/', 'Передача показань (голосом або онлайн); обслуговує близько 60% Чернігова й 19 населених пунктів')],
      scope={'chernihiv': 'близько 60% міста — перевірте назву постачальника у своєму рахунку'}),
    S('sumy-teplo', 'Сумитеплоенерго', 'utility', 'https://teplo.sumy.ua/', ['sumy'], ['heat'], A(reg=True), 'partial',
      [('https://teplo.sumy.ua/', 'Технічні роботи на сайті; доступне посилання на особистий кабінет')]),
    S('ifteplo', 'ДМП «Івано-Франківськтеплокомуненерго»', 'utility', 'https://tke.if.ua/', ['ivano-frankivsk'], ['heat'], A(debt=None), 'partial',
      [('https://tke.if.ua/', 'Розділи «Показники», «Заборгованість»; довідка щодо боргу телефоном')]),
    S('rivne-teplo', 'Рівнетеплоенерго — особистий кабінет', 'utility', 'http://rivneteploenergo.com/', ['rivne'], ['heat'],
      A(readings=True, history=True, bill=True, reg=True), 'partial',
      [('http://rivneteploenergo.com/', '«Особистий кабінет»: реєстр нарахувань і оплат, запис показників, PDF-квитанція')],
      limits='Сайт давно не оновлювався — перевіряйте актуальність телефоном абонентської служби.'),
    S('kr-teplo', 'КП «Теплоенергетик» (Кропивницький)', 'utility', 'https://teploenergetik.kr.ua/', ['kropyvnytskyi'], ['heat'], A(reg=True), 'partial',
      [('https://teploenergetik.kr.ua/', 'Посилання «Особистий кабінет»')]),
    S('cv-teplo', 'Чернівцітеплокомуненерго', 'utility', 'https://teplo.cv.ua/', ['chernivtsi'], ['heat'], A(reg=True), 'partial',
      [('https://teplo.cv.ua/', 'Посилання «Особистий кабінет»')]),

    # ── Національний рівень: газ ───────────────────────────────────────────────────────────
    S('gazmerezhi', '«Газмережі» — особистий кабінет', 'network', 'https://grmu.com.ua/', list(PLACES), ['gasdist'],
      A(readings=True, debt=True, reg=True), 'verified',
      [('https://grmu.com.ua/', 'Новина 24.11.2026: показання щомісяця з 1 до 5 числа, нарахування й заборгованість за розподіл газу, застосунок «Куб»')],
      operator='ТОВ «Газорозподільні мережі України»', cabinet='https://my.grmu.com.ua/', app='Куб',
      limits='Лише якщо ваш оператор газорозподілу — «Газмережі» (вказано у квитанції за розподіл). Оплата самого газу — постачальнику.'),
]

# Електроенергія: постачальники універсальних послуг (ПУП) за офіційним переліком НКРЕКП.
# Це постачальник «за замовчуванням» для побутових споживачів; людина могла обрати іншого.
# Сайти й кабінети ПУП ще не перевірено — статус 'partial' до перевірки.
PUP_SOURCE = ('https://www.nerc.gov.ua/sferi-diyalnosti/elektroenergiya/promislovist/tarifi-na-elektroenergiyu-dlya-nepobutovih-spozhivachiv/'
              'tarifi-na-poslugi-postachalnikiv-universalnih-poslug/tarifi-na-poslugi-postachalnikiv-universalnih-poslug-shcho-diyut-z-01-sichnya-2026-roku')
PUP = ['ЕНЕРА ВІННИЦЯ', 'ВОЛИНЬЕЛЕКТРОЗБУТ', 'ДНІПРОВСЬКІ ЕНЕРГЕТИЧНІ ПОСЛУГИ', 'ДОНЕЦЬКІ ЕНЕРГЕТИЧНІ ПОСЛУГИ',
       'ЖИТОМИРСЬКА ОБЛАСНА ЕНЕРГОПОСТАЧАЛЬНА КОМПАНІЯ', 'ЗАКАРПАТТЯЕНЕРГОЗБУТ', 'ЗАПОРІЖЖЯЕЛЕКТРОПОСТАЧАННЯ',
       'КИЇВСЬКІ ЕНЕРГЕТИЧНІ ПОСЛУГИ', 'КИЇВСЬКА ОБЛАСНА ЕНЕРГОПОСТАЧАЛЬНА КОМПАНІЯ', 'КІРОВОГРАДСЬКА ОБЛАСНА ЕНЕРГОПОСТАЧАЛЬНА КОМПАНІЯ',
       'ЕНЕРА СХІД', 'ЛЬВІВЕНЕРГОЗБУТ', 'МИКОЛАЇВСЬКА ЕЛЕКТРОПОСТАЧАЛЬНА КОМПАНІЯ', 'ОДЕСЬКА ОБЛАСНА ЕНЕРГОПОСТАЧАЛЬНА КОМПАНІЯ',
       'ПОЛТАВАЕНЕРГОЗБУТ', 'ПРИКАРПАТЕНЕРГОТРЕЙД', 'РІВНЕНСЬКА ОБЛАСНА ЕНЕРГОПОСТАЧАЛЬНА КОМПАНІЯ', 'ЕНЕРА СУМИ',
       'ТЕРНОПІЛЬЕЛЕКТРОПОСТАЧ', 'ХАРКІВЕНЕРГОЗБУТ', 'ХЕРСОНСЬКА ОБЛАСНА ЕНЕРГОПОСТАЧАЛЬНА КОМПАНІЯ', 'ХМЕЛЬНИЦЬКЕНЕРГОЗБУТ',
       'ЧЕРКАСИЕНЕРГОЗБУТ', 'ЧЕРНІВЕЦЬКА ОБЛАСНА ЕНЕРГОПОСТАЧАЛЬНА КОМПАНІЯ', 'ЕНЕРА ЧЕРНІГІВ']

# Хто стоїть за сервісом — лише те, що видно з джерела. 'municipal' показуємо як «комунальне підприємство»,
# 'private' — «приватна компанія», None — нічого не стверджуємо.
OWNER = {
    'ckc-kyiv': 'municipal', 'gioc-kyiv': 'municipal', 'mycity-khm': 'municipal', 'kte-kyiv': 'municipal',
    'kharkivvodokanal': 'municipal', 'zp-vodokanal': 'municipal', 'lviv-vodokanal': 'municipal', 'dnipro-kirovograd': 'municipal',
    'poltava-vodokanal': 'municipal', 'cherkasy-vodokanal': 'municipal', 'chernivtsi-vodokanal': 'municipal', 'khm-vodokanal': 'municipal',
    'kherson-vodokanal': 'municipal', 'hts-kharkiv': 'municipal', 'teploenergo-dnipro': 'municipal', 'teplo-odesa': 'municipal',
    'lte-lviv': 'municipal', 'ifteplo': 'municipal', 'kr-teplo': 'municipal', 'cv-teplo': 'municipal',
    'novakom': 'private', 'mirc-mykolaiv': 'private', 'erckp-dnipro': 'private', 'gerc-odesa': 'private', 'infoxvodokanal': 'private',
}
# Не публікуємо: 'unconfirmed' + записи, що дублюють інший (портал Львова — це кабінет Львівводоканалу).
NOT_PUBLISHED = {'infolviv': 'дублює lviv-vodokanal (той самий портал)',
                 'gioc-kyiv': 'gioc.kiev.ua тепер переадресовує на gioc.kyivcity.gov.ua — сайт про цифрові сервіси міста; кабінету для оплати комуналки там не знайдено (27.11.2026)'}
for _s in SERVICES:
    _s['owner'] = OWNER.get(_s['id'])
    if _s['type'] == 'unified' and _s['id'] != 'infolviv':
        _s['util'] = ['multi']   # перелік послуг єдиного рахунку джерелом не підтверджено


def published():
    return [s for s in SERVICES if s['status'] in ('verified', 'partial') and s['id'] not in NOT_PUBLISHED]

OFFICIAL_HOST_HINT = ('.gov.ua', 'vodokanal', 'teplo', 'grmu.com.ua', 'novakom.com.ua')


def check():
    """Правила бази: без дублів, кожен сервіс має джерело, місто з довідника, валідні типи й можливості."""
    ids = set(); errs = []
    for s in SERVICES:
        if s['id'] in ids: errs.append(f'дубль {s["id"]}')
        ids.add(s['id'])
        if s['type'] not in TYPES: errs.append(f'{s["id"]}: тип')
        if not s['sources']: errs.append(f'{s["id"]}: немає джерела')
        if not s['url'].startswith('http'): errs.append(f'{s["id"]}: url')
        for p in s['places'] + list(s['scope']):
            if p not in PLACES: errs.append(f'{s["id"]}: місто {p}')
        for u in s['util']:
            if u not in UTIL: errs.append(f'{s["id"]}: послуга {u}')
        if s['status'] == 'verified' and not any(v for k, v in s['actions'].items() if k != 'register'):
            errs.append(f'{s["id"]}: verified без підтвердженої дії')
        if s['type'] == 'payment' and s['owner'] == 'municipal':
            errs.append(f'{s["id"]}: платіжний сервіс позначено як комунальний')
        if s['type'] == 'payment' and s['status'] == 'verified':
            errs.append(f'{s["id"]}: платіжний сервіс не може бути «офіційним» без рішення міста')
    return errs


def for_place(pid, util=None, only_verified=True):
    """Що показати людині: спершу єдиний рахунок міста, потім кабінети постачальників, потім національні."""
    order = {'unified': 0, 'utility': 1, 'network': 2, 'supplier': 3, 'payment': 9}
    out = [s for s in (published() if not only_verified else SERVICES) if pid in s['places'] and (not only_verified or s['status'] == 'verified')
           and (util is None or util in s['util']) and s['type'] != 'payment']
    return sorted(out, key=lambda s: (order[s['type']], s['name']))


if __name__ == '__main__':
    import collections, sys
    sys.stdout.reconfigure(encoding='utf-8')
    print('errors:', check())
    c = collections.Counter(s['status'] for s in SERVICES); print('services:', len(SERVICES), dict(c))
    for pid, p in PLACES.items():
        v = [s['id'] for s in for_place(pid) if s['type'] != 'network']
        allv = [s['id'] for s in SERVICES if pid in s['places'] and s['type'] != 'network']
        print(f'{p["name"]:18} verified: {", ".join(v) or "—"}   | all: {len(allv)}')
