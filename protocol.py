import asn1tools

asn1_compiler = asn1tools.compile_files(["../smm3ng-types/smm3ng-types.asn1",
                                         "../smm3ng-protocol/smm3ng-protocol.asn1"], codec="der")
