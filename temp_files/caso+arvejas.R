# Crear un vector con los datos de los pesos de las compras 
# de arvejas de los clientes
pesos <- c(1.98,0.75,1.20,1.37,1.22,0.95,2.13,0.95,2.74,0.97,
           1.92,3.14,0.50,0.87,0.94,1.37,0.87,0.26,0.30,1.93,
           0.86,0.41,0.92,1.84,2.58,0.81,0.88,0.41,1.26,0.73,
           1.26,1.42,1.68,0.74,1.29,0.42,0.68,0.65,0.30,1.02,
           1.11,0.83,1.46,0.70,0.50,1.24,0.67,2.06,0.81,1.39,
           1.17,0.68,2.20,1.38,1.05,1.15,1.40,1.05,0.22,1.15,
           0.83,1.10,1.34,2.01,0.70,1.92,1.18,1.68,1.58,1.43,
           0.59,0.96,1.37,0.62,0.76,1.34,1.47,1.26,0.64,0.58,
           2.13,1.14,1.05,0.94,0.55,1.36,0.90,0.91,1.59,1.51,
           2.01,0.79,1.38,2.00,0.57,0.65,0.57,0.48,1.04,1.39,
           1.82,1.69,0.61,2.52,0.72,1.05,0.81,0.94,1.10,1.06,
           0.99,1.06,0.78,0.78,0.44,0.83,0.77,3.86,0.51,1.07,
           0.47,0.48,1.06,0.61,1.00,0.81,0.74,0.36,0.54,1.09,
           1.33,0.78,1.00,1.75,2.05,0.58,0.94,1.82,0.79,0.97,
           0.96,0.64,0.80,0.99,0.81,1.74,0.79,0.81,1.42,0.59,
           0.98,0.46,1.79,0.87,0.79,0.54,1.00,0.67,0.77,1.90,
           0.92,0.59,1.09,0.83,1.34,2.05,0.61,1.26,1.04,1.56,
           0.89,1.52,0.42,2.33,1.54,0.93,0.48,1.38,1.27,1.00,
           1.08,0.75,1.20,1.16,0.87,0.51,1.42,1.32,0.66,0.45,
           1.11,0.84,1.13,0.52,0.62,1.72,1.22,1.34,2.48,1.07)
# Visualizar la distribución de los datos
hist(pesos, breaks = 20, prob = TRUE, col = 'blue', border = 'black', main = 'Distribución de Peso de Arvejas',
     xlab = 'Peso (kg)', ylab = 'Frecuencia Relativa')

# agrupar los datos en intervalos de acuerdo a la prorpuesta

cortes <- c(0, 0.5, 1, 1.5, 2, max(pesos))
grupo <- cut(pesos,breaks = cortes)
table(grupo)

#realizamos un gráfico de barras de la distribución de compras
#según el peso, agrupado en intervalos. Nota: este gráfico es una
#representación algo abusiva de los datos ya que estos son
#cuantitativos continuos.

barplot(table(grupo))

#para encontrar frecuencias reltativas
frec.relativas <- table(grupo)/sum(table(grupo))
barplot(frec.relativas)
