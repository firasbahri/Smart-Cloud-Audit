import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import { createPinia } from 'pinia'
import PrimeVue from 'primevue/config'
import Aura from '@primeuix/themes/aura'
import { ToastService } from 'primevue'
import 'primeicons/primeicons.css'
import 'primeflex/primeflex.css'

const pinia = createPinia()
const app = createApp(App)

app.use(pinia)
app.use(router)
app.use(PrimeVue, {
	theme: {
		preset: Aura,
		options: {
			darkModeSelector: ':root'
		}
	}
})
app.use(ToastService)
app.mount('#app')