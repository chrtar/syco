[farepayment.com_arecords]
superadmin.active.production.nsg:81.201.214.13
superadmin.passive.production.nsg:81.201.214.13
superadmin.active.production.tc:88.80.165.135
superadmin.passive.production.tc:88.80.165.135
superadmin.active.uat.tp:10.100.100.132
superadmin.passive.uat.tp:10.100.100.132
superadmin.active.stable.tp:10.100.100.131
superadmin.passive.stable.tp:10.100.100.131
superadmin.active.integration.tp:10.100.100.130
superadmin.passive.integration.tp:10.100.100.130
backoffice.active.production.nsg:81.201.214.13
backoffice.passive.production.nsg:81.201.214.13
backoffice.active.production.tc:88.80.165.135
backoffice.passive.production.tc:88.80.165.135
backoffice.active.uat.tp:10.100.100.132
backoffice.passive.uat.tp:10.100.100.132
backoffice.active.stable.tp:10.100.100.131
backoffice.passive.stable.tp:10.100.100.131
backoffice.active.integration.tp:10.100.100.130
backoffice.passive.integration.tp:10.100.100.130
paymentservice.active.production.nsg:81.201.214.13
paymentservice.passive.production.nsg:81.201.214.13
paymentservice.active.production.tc:88.80.165.135
paymentservice.passive.production.tc:88.80.165.135
paymentservice.active.uat.tp:10.100.100.132
paymentservice.passive.uat.tp:10.100.100.132
paymentservice.active.stable.tp:10.100.100.131
paymentservice.passive.stable.tp:10.100.100.131
paymentservice.active.integration.tp:10.100.100.130
paymentservice.passive.integration.tp:10.100.100.130
spp.active.production.nsg:81.201.214.13
spp.passive.production.nsg:81.201.214.13
spp.active.production.tc:88.80.165.135
spp.passive.production.tc:88.80.165.135
spp.active.uat.tp:10.100.100.132
spp.passive.uat.tp:10.100.100.132
spp.active.stable.tp:10.100.100.131
spp.passive.stable.tp:10.100.100.131
spp.active.integration.tp:10.100.100.130
spp.passive.integration.tp:10.100.100.130
diagnostics.active.production.nsg:81.201.214.13
diagnostics.passive.production.nsg:81.201.214.13
diagnostics.active.production.tc:88.80.165.135
diagnostics.passive.production.tc:88.80.165.135
diagnostics.active.uat.tp:10.100.100.132
diagnostics.passive.uat.tp:10.100.100.132
diagnostics.active.stable.tp:10.100.100.131
diagnostics.passive.stable.tp:10.100.100.131
diagnostics.active.integration.tp:10.100.100.130
diagnostics.passive.integration.tp:10.100.100.130

[farepayment.com_cname]
superadmin:backoffice.active.production.$DATA_CENTER$  
backoffice:backoffice.active.production.$DATA_CENTER$  
paymentservice:paymentservice.active.production.$DATA_CENTER$
spp:spp.active.production.$DATA_CENTER$
diagnostics:diagnostics.active.production.$DATA_CENTER$
