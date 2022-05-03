{
	"name" : "Add Gen Bus Posting Group field in res.partner",
	"version" : "1.0",
	"summary" : "Add Gen Bus  Posting Group field in res.partner",
	"sequence" : 0,
	"author" : "Muriel Rémi Cyr",
	"license" : "LGPL-3",
	"description" : """
		This module adds a new field 'gen_bus_pg' field in the res.partner model
	""",
	"data" : [
		"views/partner.xml"
	],
	"depends" : ["base"],
	"installable" : True,
	"application" : True,
	"auto_install" : False
}