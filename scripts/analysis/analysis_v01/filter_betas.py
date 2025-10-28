import scipy

def filter_betas(spmmat, beta_images, bayesian=False):

	no_interest_regressors = ['Realign', 'Outlier', 'keypress', ')x']
	
	SPM         = scipy.io.loadmat(spmmat)
	spm_beta_ix = 15 if bayesian else 13               
	beta_names  = [r[5][0] for r in SPM['SPM'][0,0][spm_beta_ix][0]]

	filtered_betas, descriptions = [], []
	for d, b in zip(beta_names, beta_images):
		
		if not any([r in d for r in no_interest_regressors]):
			run_n_ix0 = d.find('Sn(') + 3
			run_n_ix1 = int(d[run_n_ix0:].find(')') + run_n_ix0)
			run_n     = int(d[run_n_ix0:run_n_ix1])
			beta_name = f'{d[(run_n_ix1+2):]}_run-{run_n:02d}'

			for s0, s1 in [('*bf(1)', ''), ('*bf(2)', '-hrfder1'), ('*bf(3)', '-hrfder2'), ('^1', '')]:
				beta_name = beta_name.replace(s0, s1)
			filtered_betas.append(b)
			descriptions.append(beta_name)

	return filtered_betas, descriptions