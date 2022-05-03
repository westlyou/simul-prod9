{
	"name" : "Add Posting Group field in res.partner",
	"version" : "1.0",
	"summary" : "Add Posting Group field in res.partner",
	"sequence" : 0,
	"author" : "Muriel Rémi Cyr",
	"license" : "LGPL-3",
	"description" : """
		This module adds a new field 'posting_group' field in the res.partner model
	""",
	"data" : [
		"views/partner.xml"
	],
	"depends" : [],
	"installable" : True,
	"application" : True,
	"auto_install" : False
}